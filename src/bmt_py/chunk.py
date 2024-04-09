from typing import Callable, Optional, Union

from pydantic import BaseModel, ConfigDict, field_validator

from bmt_py.span import DEFAULT_SPAN_SIZE, make_span
from bmt_py.utils import assert_flex_bytes, keccak256_hash, serialize_bytes

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
    model_config = ConfigDict(arbitrary_types_allowed=True)
    message: Union[str, list[Union[int, bytes]], bytes, bytearray]

    # Add a custom validator to ensure that the message is of the correct type
    @field_validator("message")
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

    model_config = ConfigDict(arbitrary_types_allowed=True)

    payload: bytes
    max_payload_length: int
    span_length: int
    data: Callable[[], bytes]
    span: Callable[[], bytes]
    address: Callable[[], bytes]
    inclusion_proof: Callable[[int], list[bytes]]
    bmt: Callable[[], bytes]


def bmt(payload: bytes, options: Optional[dict] = None) -> list[bytes]:
    """
    Gives back all levels of the binary Merkle tree (BMT) of the payload.

    Args:
        chunk_data: Any data in bytes object
        options: Function configurations, including a custom hash function
    Returns:
        Array of the whole BMT hash level of the given data.
            First level is the data itself until the last level that is the root hash itself.
    """
    if len(payload) > DEFAULT_MAX_PAYLOAD_SIZE:
        msg = f"invalid data length {len(payload)}"
        raise ValueError(msg)

    hash_function = options.get("hashFn", keccak256_hash) if options else keccak256_hash

    # Create a buffer padded with zeros
    padded_data = payload + b"\x00" * (DEFAULT_MAX_PAYLOAD_SIZE - len(payload))
    bmt_tree = []

    while len(padded_data) != HASH_SIZE:
        bmt_tree.append(padded_data)
        hashed_data = bytearray(len(padded_data) // 2)

        # In each round, we hash the segment pairs together
        for offset in range(0, len(padded_data), SEGMENT_PAIR_SIZE):
            hash_result = hash_function(padded_data[offset : offset + SEGMENT_PAIR_SIZE])
            hashed_data[offset // 2 : offset // 2 + len(hash_result)] = hash_result

        padded_data = hashed_data

    # Add the last "padded_data" that is the BMT root hash of the application
    bmt_tree.append(padded_data)

    return bmt_tree


def inclusion_proof_bottom_up(payload_bytes: bytes, segment_index: int, options: Optional[dict] = None) -> list[bytes]:
    """
    Gives back required segments for inclusion proof of a given payload byte index.

    Args:
        payload_bytes: Chunk data initialized in bytes object
        segment_index: Segment index in the data array that has to be proofed for inclusion
        options: Function configuration
    Returns:
        Required segments for inclusion proof starting from the data level until the BMT root hash of the payload
    """
    if segment_index * SEGMENT_SIZE >= len(payload_bytes):
        msg = f"The given segment index {segment_index} is greater than {len(payload_bytes) // SEGMENT_SIZE}"
        raise ValueError(msg)

    tree = bmt(payload_bytes, options)
    sister_segments = []
    root_hash_level = len(tree) - 1
    for level in range(root_hash_level):
        merge_coefficient = 1 if segment_index % 2 == 0 else -1
        sister_segment_index = segment_index + merge_coefficient
        sister_segment = tree[level][sister_segment_index * SEGMENT_SIZE : (sister_segment_index + 1) * SEGMENT_SIZE]
        sister_segments.append(sister_segment)
        # Update segment_index for the next iteration
        segment_index >>= 1

    return sister_segments


def root_hash_from_inclusion_proof(
    proof_segments: list,
    prove_segment: bytes,
    prove_segment_index: int,
    options: Optional[dict] = None,
) -> bytes:
    """
    Calculates the BMT root hash from the provided inclusion proof segments and its corresponding segment index.

    Args:
        proof_segments: List of inclusion proof segments as bytes objects
        prove_segment: The segment to be proven as bytes
        prove_segment_index: The index of the segment to be proven
        options: Function configurations, including a custom hash function

    Returns:
        The calculated BMT root hash as bytes
    """
    hash_function = options.get("hashFn", keccak256_hash) if options else keccak256_hash

    calculated_hash = prove_segment
    for proof_segment in proof_segments:
        merge_segment_from_right = prove_segment_index % 2 == 0
        calculated_hash = (
            hash_function(calculated_hash, proof_segment)
            if merge_segment_from_right
            else hash_function(proof_segment, calculated_hash)
        )
        prove_segment_index >>= 1

    return calculated_hash


def bmt_root_hash(
    chunk_data: bytes,
    max_payload_length: int = DEFAULT_MAX_PAYLOAD_SIZE,
    options: Optional[dict] = None,
) -> bytes:
    """
    Calculate the root hash of a binary Merkle tree (BMT) from the chunk data.

    Args:
        chunk_data (bytes): Chunk data as bytes
        max_payload_length (int): Maximum payload length, defaults to DEFAULT_MAX_PAYLOAD_SIZE
        options (Optional dict): Function configurations, including a custom hash function

    Returns:
        The root hash of the binary Merkle tree as bytes
    """
    if len(chunk_data) > max_payload_length:
        msg = f"invalid data length {len(chunk_data)}"
        raise ValueError(msg)

    hash_function = options.get("hashFn", keccak256_hash) if options else keccak256_hash

    # Create a buffer padded with zeros
    padded_data = chunk_data + b"\x00" * (max_payload_length - len(chunk_data))

    while len(padded_data) != HASH_SIZE:
        hashed_data = bytearray(len(padded_data) // 2)

        # In each round, we hash the segment pairs together
        for offset in range(0, len(padded_data), SEGMENT_PAIR_SIZE):
            hash_result = hash_function(padded_data[offset : offset + SEGMENT_PAIR_SIZE])
            hashed_data[offset // 2 : offset // 2 + len(hash_result)] = hash_result

        padded_data = hashed_data

    return padded_data


def chunk_address(
    payload_bytes: bytes,
    span_length: Optional[int],
    chunk_span: Optional[bytes],
    options: Optional[dict] = None,
) -> bytes:
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
        options: function configuraiton

    Returns:
        The Chunk address in a byte array
    """
    if chunk_span is None:
        span_length = span_length if span_length else None
        chunk_span = make_span(len(payload_bytes), span_length)

    hash_function = options.get("hashFn", keccak256_hash) if options else keccak256_hash

    root_hash = bmt_root_hash(payload_bytes, 4096, {"hashFn": hash_function})
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

    padding_chunked_len = (max_payload_length - len(payload_bytes)) * b"\0"

    # Function/Method definitions.
    def span() -> bytes:
        return make_span(starting_span_value, span_length)

    def data() -> bytes:
        return serialize_bytes(payload_bytes, bytes(padding_chunked_len))

    def inclusion_proof(segment_index: int) -> list[bytes]:
        return inclusion_proof_bottom_up(data(), segment_index, {"hash_fn": hash_fn})

    def address() -> bytes:
        return chunk_address(payload_bytes, span_length, span(), {"hash_fn": hash_fn})

    def _bmt() -> list[bytes]:
        return bmt(payload_bytes, {"hash_fn": hash_fn})

    return Chunk(
        payload=payload_bytes,
        max_payload_length=max_payload_length,
        span_length=span_length,
        data=data,
        span=span,
        address=address,
        inclusion_proof=inclusion_proof,
        bmt=_bmt,
    )
