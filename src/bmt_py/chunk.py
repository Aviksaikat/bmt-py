from typing import Callable, Optional, Union

from pydantic import BaseModel, validator

from bmt_py.span import DEFAULT_SPAN_SIZE, make_span
from bmt_py.utils import FlexBytes, assert_flex_bytes, keccak256_hash

# * Constants
SEGMENT_SIZE = 32
SEGMENT_PAIR_SIZE = 2 * SEGMENT_SIZE
DEFAULT_MAX_PAYLOAD_SIZE = 4096
HASH_SIZE = 32
DEFAULT_MIN_PAYLOAD_SIZE = 1


class ChunkAddress(BaseModel):
    address: bytes


class ValidChunkData(BaseModel):
    data: bytes


class Message(BaseModel):
    message: Union[str, list[Union[int, bytes]], bytes, bytearray]

    # Add a custom validator to ensure that the message is of the correct type
    @validator("message")
    def validate_message_type(cls, v):  # noqa: N805
        if not isinstance(v, (str, list, bytes, bytearray)):
            msg = f"The message must be a string, a list, bytes, or a bytearray, not {type(v)}"
            raise ValueError(msg)
        return v


class Options(BaseModel):
    hash_fn: Optional[Callable[[list[Message]], bytes]] = None


class Chunk(BaseModel):
    """
    * General chunk class for Swarm

    It stores the serialized data and provides functions to access
    the fields of a chunk.

    It also provides an address function to calculate the address of
    the chunk that is required for the Chunk API.

    Attributes:
        payload: FlexBytes
        max_payload_length: int
        span_length: int
        data: ChunkData
        span: Bytes
        address: ChunkAddress
        inclusion_proof: List[Any]
        bmt: List[Any]

    Notes:
        This class extends Pydantic's :class:`BaseModel`.

        The inputs for missing attributes will be set to None if not provided
        during object creation.
    """

    payload: FlexBytes
    max_payload_length: int
    span_length: int
    data: ValidChunkData
    span: Callable[[], bytes]
    address: Callable[[], ChunkAddress]
    inclusion_proof: Callable[[int], bytes]
    bmt: Callable[[], bytes]

    class Config:
        arbitrary_types_allowed = True


def bmt_function(payload: bytes, options: Optional[dict] = None): ...
def inclusion_proof_bottom_up(payload_byyes: bytes, segment_index: int, options: Optional[dict] = None): ...


def bmt_root_hash(chunk_data: bytes, max_payload_length: int = DEFAULT_MAX_PAYLOAD_SIZE, options=None) -> bytes:
    """
    Calculate the root hash of a binary Merkle tree (BMT) from the chunk data.

    :param chunk_data: Chunk data as bytes
    :param max_payload_length: Maximum payload length, defaults to DEFAULT_MAX_PAYLOAD_SIZE
    :param options: Function configurations, including a custom hash function

    :returns: The root hash of the binary Merkle tree as bytes
    """
    if len(chunk_data) > max_payload_length:
        msg = f"invalid data length {len(chunk_data)}"
        raise ValueError(msg)

    hash_function = options.get("hashFn", keccak256_hash) if options else keccak256_hash

    # Create a buffer padded with zeros
    padded_data = chunk_data + b"\x00" * (max_payload_length - len(chunk_data))
    hash_size = 32  # Assuming a 256-bit hash size
    segment_pair_size = 64  # Assuming 32-byte segments

    while len(padded_data) != hash_size:
        hashed_data = bytearray(len(padded_data) // 2)

        # In each round, we hash the segment pairs together
        for offset in range(0, len(padded_data), segment_pair_size):
            hash_result = hash_function(padded_data[offset : offset + segment_pair_size])
            hashed_data[offset // 2 : offset // 2 + len(hash_result)] = hash_result

        padded_data = hashed_data

    return padded_data


def chunk_address(
    payload_bytes: bytes,
    span_length: Optional[int],
    chunk_span: Optional[bytes],
    options: Optional[dict] = None,
):
    """
    Calculate the chunk address from the Binary Merkle Tree of the chunk data

    The BMT chunk address is the hash of the 8-byte span and the root
    hash of a binary Merkle tree (BMT) built on the 32-byte segments
    of the underlying data.

    If the chunk content is less than 4k, the hash is calculated
    as if the chunk was padded with all zeros up to 4096 bytes.

    Args:
        payload: Chunk data bytes
        span_length: Dedicated byte length for serializing span value of chunk
        chunk_span: Constructed Span bytes object of the chunk
        hash_fn: Function for hash calculations

    Returns:
        The Chunk address in a byte array
    """
    if chunk_span is None:
        chunk_span = make_span(len(payload_bytes), span_length)

    hash_function = options.get("hashFn", keccak256_hash) if options else keccak256_hash

    root_hash = bmt_root_hash(payload_bytes, 4096, hash_function)
    chunk_hash_input = bytes(chunk_span + root_hash)

    return hash_function(chunk_hash_input)


def make_chunk(
    payload_bytes: bytes,
    options: Optional[dict] = None,
) -> Chunk:
    # Default options.
    options = options or {}
    max_payload_length = options.get("maxPayloadSize", DEFAULT_MAX_PAYLOAD_SIZE)
    span_length = options.get("spanLength", DEFAULT_SPAN_SIZE)
    starting_span_value = options.get("startingSpanValue", len(payload_bytes))
    hash_fn = options.get("hashFn", keccak256_hash)

    # Assertions.
    if not assert_flex_bytes(payload_bytes, 0, max_payload_length):
        msg = f"Invalid FlexBytes: b is {payload_bytes!r}, min_length is {0}, max_length is {max_payload_length}."
        raise TypeError(msg)

    payload_bytes = (max_payload_length - len(payload_bytes)) * b"\0"

    # Function/Method definitions.
    def span() -> bytes:
        return make_span(starting_span_value, span_length)

    def data() -> bytes:
        return payload_bytes

    def inclusion_proof(segment_index: int) -> list[bytes]:
        return inclusion_proof_bottom_up(payload_bytes, segment_index, {"hash_fn": hash_fn})

    def address() -> str:
        return chunk_address(payload_bytes, span_length, span(), {"hash_fn": hash_fn})

    def bmt() -> list[bytes]:
        return bmt_function(payload_bytes, {"hash_fn": hash_fn})

    return Chunk(
        payload=payload_bytes,
        max_payload_length=max_payload_length,
        span_length=span_length,
        data=data,
        span=span,
        address=address,
        inclusion_proof=inclusion_proof,
        bmt=bmt,
    )
