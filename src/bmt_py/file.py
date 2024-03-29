from math import floor, log2
from typing import Callable, Optional

from pydantic import BaseModel

from bmt_py.chunk import (
    DEFAULT_MAX_PAYLOAD_SIZE,
    SEGMENT_SIZE,
    Chunk,
    ChunkAddress,
    make_chunk,
    make_span,
)
from bmt_py.span import DEFAULT_SPAN_SIZE, get_span_value
from bmt_py.utils import keccak256_hash, serialize_bytes


class ChunkInclusionProof(BaseModel):
    """
    Represents the inclusion proof for a chunk, including the span and sister segments.
    """

    span: bytes
    sister_segments: list[bytes]


class ChunkedFile(BaseModel):
    """
    * ChunkedFile class for Swarm

    It stores the serialized data and provides functions to access
    the fields of a chunked file.

    It also provides functions to calculate the BMT and inclusion proof
    for a given chunk and its index.

    Attributes:
        leaf_chunks: List[Chunk]
        root_chunk: Chunk
        payload: bytes
        address: ChunkAddress
        span: bytes
        bmt: List[List[Chunk]]

    Notes:
        This class extends Pydantic's :class:`BaseModel`.

        The inputs for missing attributes will be set to None if not provided
        during object creation.
    """

    leaf_chunks: Callable[[], list]
    root_chunk: Callable
    payload: bytes
    address: Callable[[], ChunkAddress]
    span: Callable[[], bytes]
    bmt: Callable[[], list[list[Chunk]]]

    class Config:
        arbitrary_types_allowed = True


def pop_carrier_chunk(chunks: list[Chunk]) -> Optional[Chunk]:
    """
    Removes the carrier chunk from the given chunks array and returns it.

    :param chunks: A list of Chunk objects
    :return: The carrier chunk, or None if no carrier chunk is found
    """
    if len(chunks) <= 1:
        return None

    # Assuming Chunk is defined as a class with `max_payload_length` and `payload` attributes
    max_data_length = chunks[0].max_payload_length
    max_segment_count = max_data_length // SEGMENT_SIZE

    if len(chunks) % max_segment_count == 1:
        return chunks.pop()
    return None


def create_intermediate_chunk(
    children_chunks: list[Chunk],
    span_length: int,
    max_payload_size: int,
) -> Chunk:
    """
    Creates an intermediate chunk by combining the address bytes of the given children chunks.

    :param children_chunks: A list of Chunk objects
    :param span_length: Span length
    :param max_payload_size: Maximum payload size
    :return: A new intermediate chunk
    """
    chunk_addresses = [chunk.address() for chunk in children_chunks]
    chunk_span_sum_values = sum(get_span_value(chunk.span()) for chunk in children_chunks)
    next_level_chunk_bytes = serialize_bytes(**chunk_addresses)

    return make_chunk(
        next_level_chunk_bytes,
        {
            "spanLength": span_length,
            "startingSpanValue": chunk_span_sum_values,
            "maxPayloadSize": max_payload_size,
        },
    )


def next_bmt_level(chunks: list[Chunk], carrier_chunk: Optional[Chunk] = None) -> dict:
    """
    Calculates the next level of a Binary Merkle Tree (BMT) given a set of chunks and an optional carrier chunk.

    :param chunks: List of Chunk objects
    :param carrier_chunk: Optional Chunk object to be considered as a carrier chunk
    :returns: A dictionary containing the next level chunks and the next level carrier chunk
    """
    if not chunks:
        msg = "The given chunk array is empty"
        raise ValueError(msg)

    max_payload_length = chunks[0].max_payload_length
    span_length = chunks[0].span_length
    max_segment_count = max_payload_length // SEGMENT_SIZE
    next_level_chunks = []

    for offset in range(0, len(chunks), max_segment_count):
        children_chunks = chunks[offset : offset + max_segment_count]
        next_level_chunks.append(create_intermediate_chunk(children_chunks, span_length, max_payload_length))

    # Edge case handling when there is a carrierChunk
    next_level_carrier_chunk = carrier_chunk

    if carrier_chunk:
        # Try to merge carrier chunk if it's the first to its parents' payload
        if len(next_level_chunks) % max_segment_count != 0:
            next_level_chunks.append(carrier_chunk)
            next_level_carrier_chunk = None  # Merged
    else:
        # Try to pop carrier chunk if it exists on the level
        next_level_carrier_chunk = pop_carrier_chunk(next_level_chunks)

    return {
        "nextLevelChunks": next_level_chunks,
        "nextLevelCarrierChunk": next_level_carrier_chunk,
    }


def bmt_root_chunk(chunks: list[Chunk]) -> Chunk:
    """
    Calculates the root chunk of a Binary Merkle Tree (BMT) given a set of chunks.

    :param chunks: List of Chunk objects
    :returns: The root chunk of the BMT
    """
    if not chunks:
        msg = "given chunk array is empty"
        raise ValueError(msg)

    level_chunks = chunks
    carrier_chunk = pop_carrier_chunk(level_chunks)

    while len(level_chunks) != 1 or carrier_chunk:
        result = next_bmt_level(level_chunks, carrier_chunk)
        level_chunks = result["nextLevelChunks"]
        carrier_chunk = result["nextLevelCarrierChunk"]

    return level_chunks[0]


def bmt(leaf_chunks: list[Chunk]) -> list[list[Chunk]]:
    """
    Calculates the Binary Merkle Tree (BMT) given a set of leaf chunks.

    :param leaf_chunks: List of Chunk objects representing leaf chunks
    :returns: A list of lists of Chunk objects representing the BMT levels
    """
    if not leaf_chunks:
        msg = "given chunk array is empty"
        raise ValueError(msg)

    level_chunks = [leaf_chunks]
    carrier_chunk = pop_carrier_chunk(leaf_chunks)
    while len(level_chunks[-1]) != 1:
        result = next_bmt_level(level_chunks[-1], carrier_chunk)
        carrier_chunk = result["nextLevelCarrierChunk"]
        level_chunks.append(result["nextLevelChunks"])

    return level_chunks


def get_bmt_index_of_segment(
    segment_index: int,
    last_chunk_index: int,
    max_chunk_payload_byte_length: int = 4096,
) -> dict:
    """
    Get the chunk's position of a given payload segment index in the BMT tree.

    :param segment_index: The segment index of the payload
    :param last_chunk_index: The last chunk index on the BMT level of the segment
    :param max_chunk_payload_byte_length: Maximum byte length of a chunk. Default is 4096
    :return: A dictionary with 'level' and 'chunk_index' keys
    """
    # 128 by default
    max_segment_count = max_chunk_payload_byte_length // SEGMENT_SIZE
    # 7 by default
    chunk_bmt_levels = int(log2(max_segment_count))
    level = 0

    if (
        (segment_index // max_segment_count) == last_chunk_index
        and (  # the segment is subsumed under the last chunk
            last_chunk_index % max_segment_count
        )
        == 0
        and last_chunk_index  # the last chunk is a carrier chunk
        != 0  # there is only the root chunk
    ):
        # segment_index in carrier chunk
        segment_index >>= chunk_bmt_levels
        while (segment_index % SEGMENT_SIZE) == 0:
            level += 1
            segment_index >>= chunk_bmt_levels
    else:
        segment_index >>= chunk_bmt_levels

    return {
        "chunk_index": segment_index,
        "level": level,
    }


def file_address_from_inclusion_proof(
    prove_chunks: list[ChunkInclusionProof],
    prove_segment: bytes,
    prove_segment_index: int,
    max_chunk_payload_byte_length: int = 4096,
) -> bytes:
    """
    Calculates the file address based on the inclusion proof segments and the proved segment.

    :param prove_chunks: A list of chunk inclusion proofs
    :param prove_segment: A bytes representing the proved segment
    :param prove_segment_index: The segment index of the proved segment
    :param max_chunk_payload_byte_length: Maximum byte length of a chunk. Default is 4096
    :return: The calculated file address
    """
    max_segment_count = max_chunk_payload_byte_length // SEGMENT_SIZE
    chunk_bmt_levels = log2(max_segment_count)

    file_size = get_span_value(prove_chunks[-1].span)
    last_chunk_index = floor((file_size - 1) / max_chunk_payload_byte_length)
    calculated_hash = prove_segment

    for prove_chunk in prove_chunks:
        parent_chunk_index, level = get_bmt_index_of_segment(
            prove_segment_index,
            last_chunk_index,
            max_chunk_payload_byte_length,
        )

        for proof_segment in prove_chunk.sister_segments:
            merge_segment_from_right = prove_segment_index % 2 == 0
            if merge_segment_from_right:
                calculated_hash = keccak256_hash(calculated_hash, proof_segment)
            else:
                calculated_hash = keccak256_hash(proof_segment, calculated_hash)

            prove_segment_index = floor(prove_segment_index / 2)

        calculated_hash = keccak256_hash(prove_chunk.span, calculated_hash)

        # this line is necessary if the prove_segment_index was in a carrierChunk
        prove_segment_index = parent_chunk_index

        last_chunk_index = last_chunk_index >> (chunk_bmt_levels + level * chunk_bmt_levels)

    return calculated_hash


def file_inclusion_proof_bottom_up(
    chunked_file: ChunkedFile,
    segment_index: int,
) -> list[ChunkInclusionProof]:
    """
    Gives back required sister segments of a given payload segment index for inclusion proof.

    :param chunked_file: The chunked file object
    :param segment_index: The segment index of the payload
    :return: A list of chunk inclusion proofs
    """
    if segment_index * SEGMENT_SIZE >= get_span_value(chunked_file.span()):
        msg = f"The given segment index {segment_index} is greater than {get_span_value(chunked_file.span()) // SEGMENT_SIZE}"  # noqa: E501

        raise ValueError(msg)

    level_chunks = chunked_file.leaf_chunks()
    max_chunk_payload = level_chunks[0].max_payload_length
    max_segment_count = max_chunk_payload // SEGMENT_SIZE
    chunk_bmt_levels = int(log2(max_segment_count))
    carrier_chunk = pop_carrier_chunk(level_chunks)
    chunk_inclusion_proofs = []

    while len(level_chunks) != 1 or carrier_chunk:
        chunk_segment_index = segment_index % max_segment_count
        chunk_index_for_proof = segment_index // max_segment_count

        if chunk_index_for_proof == len(level_chunks):
            if not carrier_chunk:
                msg = "Impossible"
                raise ValueError(msg)
            segment_index >>= chunk_bmt_levels
            while segment_index % max_segment_count == 0:
                next_level_chunks, next_level_carrier_chunk = next_bmt_level(level_chunks, carrier_chunk)
                level_chunks = next_level_chunks
                carrier_chunk = next_level_carrier_chunk
                segment_index >>= chunk_bmt_levels

            chunk_index_for_proof = len(level_chunks) - 1

        chunk = level_chunks[chunk_index_for_proof]
        sister_segments = chunk.inclusion_proof(chunk_segment_index)
        chunk_inclusion_proofs.append(
            ChunkInclusionProof.model_validate({"sister_segments": sister_segments, "span": chunk.span()})
        )
        segment_index = chunk_index_for_proof

        next_level_chunks, next_level_carrier_chunk = next_bmt_level(level_chunks, carrier_chunk)
        level_chunks = next_level_chunks
        carrier_chunk = next_level_carrier_chunk

    sister_segments = level_chunks[0].inclusion_proof(segment_index)
    chunk_inclusion_proofs.append(
        ChunkInclusionProof.model_validate({"sister_segments": sister_segments, "span": level_chunks[0].span()})
    )

    return chunk_inclusion_proofs


def make_chunked_file(payload: bytes, options: Optional[dict] = None) -> ChunkedFile:
    """
    Creates an object for performing BMT functions on payload data.

    :param payload: The byte array of the data.
    :param options: The settings for the used chunks.
    :return: A `ChunkedFile` object with helper methods.
    """
    options = options or {}
    max_payload_length = options.get("max_payload_length", DEFAULT_MAX_PAYLOAD_SIZE)
    span_length = options.get("span_length", DEFAULT_SPAN_SIZE)

    # splitter
    def leaf_chunks() -> list[Chunk]:
        chunks = []
        if len(payload) == 0:
            chunks.append(make_chunk(b"", options))
        else:
            for offset in range(0, len(payload), max_payload_length):
                chunks.append(make_chunk(payload[offset : offset + max_payload_length], options))
        return chunks

    def span() -> bytes:
        return make_span(len(payload), span_length)

    def address() -> ChunkAddress:
        return bmt_root_chunk(leaf_chunks()).address()

    def root_chunk() -> Chunk:
        return bmt_root_chunk(leaf_chunks())

    def _bmt() -> list[list[Chunk]]:
        return bmt(leaf_chunks())

    return ChunkedFile(
        payload=payload,
        leaf_chunks=leaf_chunks,
        span=span,
        address=address,
        root_chunk=root_chunk,
        bmt=_bmt,
    )
