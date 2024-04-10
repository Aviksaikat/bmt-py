from pathlib import Path

import pytest
from bmt_py import (
    bytes_to_hex,
    file_address_from_inclusion_proof,
    file_inclusion_proof_bottom_up,
    get_bmt_index_of_segment,
    get_span_value,
    make_chunked_file,
)
from bmt_py.chunk import SEGMENT_SIZE


@pytest.mark.parametrize(
    "payload, expected_span",
    [(bytes([1, 2, 3]), bytes([3, 0, 0, 0, 0, 0, 0, 0]))],
)
def test_chunked_file_with_lesser_than_4KB_of_data(  # noqa: N802
    payload, expected_span
):
    chunked_file = make_chunked_file(payload)

    assert len(chunked_file.leaf_chunks()) == 1
    only_chunk = chunked_file.leaf_chunks()[0]
    assert only_chunk.payload == payload
    assert only_chunk.span() == expected_span
    assert only_chunk.span() == chunked_file.span()
    assert only_chunk.address() == chunked_file.address()


def test_chunked_file_with_greater_than_4KB_of_data(bos_bytes):  # noqa: N802
    file_bytes = bos_bytes

    chunked_file = make_chunked_file(file_bytes)

    assert get_span_value(chunked_file.span()) == 15726634
    assert get_span_value(bytearray([42, 248, 239, 0, 0, 0, 0, 0])) == 15726634

    tree = chunked_file.bmt()
    assert len(tree) == 3
    assert len(tree[2]) == 1  # last level only contains the root_chunk

    root_chunk = tree[2][0]
    second_level_first_chunk = tree[1][0]  # first intermediate chunk on the first intermediate chunk level
    assert get_span_value(second_level_first_chunk.span()) == 4096 * (4096 / SEGMENT_SIZE)
    assert root_chunk.payload[:32] == second_level_first_chunk.address()
    assert len(second_level_first_chunk.payload) == 4096
    assert second_level_first_chunk.payload[:32] == tree[0][0].address()

    assert len(chunked_file.root_chunk().payload) == 960

    assert (
        bytes_to_hex(chunked_file.address(), 64)  # type: ignore
        # bee generated hash
        == "b8d17f296190ccc09a2c36b7a59d0f23c4479a3958c3bb02dc669466ec919c5d"
    )


def test_find_bmt_position_of_payload_segment_index(carrier_chunk_file_bytes):
    file_bytes = carrier_chunk_file_bytes
    chunked_file = make_chunked_file(file_bytes)
    tree = chunked_file.bmt()
    leaf_chunks = chunked_file.leaf_chunks()

    # Check whether the last chunk is not present in the BMT tree 0 level -> carrierChunk
    assert len(tree[0]) == len(leaf_chunks) - 1

    carrier_chunk = leaf_chunks.pop()
    segment_index = (len(file_bytes) - 1) // 32  # Last segment index as well
    last_chunk_index = (len(file_bytes) - 1) // 4096
    segment_id_in_tree = get_bmt_index_of_segment(segment_index, last_chunk_index)

    assert segment_id_in_tree[0] == 1
    assert segment_id_in_tree[1] == 1
    assert tree[segment_id_in_tree[0]][segment_id_in_tree[1]].address() == carrier_chunk.address()


def test_collect_required_segments_for_inclusion_proof(carrier_chunk_file_bytes):
    file_bytes = carrier_chunk_file_bytes
    chunked_file = make_chunked_file(file_bytes)
    file_hash = chunked_file.address()

    # Segment to prove
    segment_index = (len(file_bytes) - 1) // 32

    # Check segment array length for carrierChunk inclusion proof
    proof_chunks = file_inclusion_proof_bottom_up(chunked_file, segment_index)
    assert len(proof_chunks) == 2  # 1 level is skipped because the segment was in a carrierChunk

    def test_get_file_hash(segment_index):
        proof_chunks = file_inclusion_proof_bottom_up(chunked_file, segment_index)
        prove_segment = file_bytes[segment_index * SEGMENT_SIZE : segment_index * SEGMENT_SIZE + SEGMENT_SIZE]
        # Padding
        prove_segment += bytearray(SEGMENT_SIZE - len(prove_segment))

        # Check the last segment has the correct span value.
        file_size_from_proof = get_span_value(proof_chunks[-1].span)
        assert file_size_from_proof == len(file_bytes)

        return file_address_from_inclusion_proof(proof_chunks, prove_segment, segment_index)

    # Edge case
    hash1 = test_get_file_hash(segment_index)
    assert hash1 == file_hash
    hash2 = test_get_file_hash(1000)
    assert hash2 == file_hash


def test_collect_required_segments_for_inclusion_proof_2(bos_bytes):
    file_bytes = bos_bytes
    chunked_file = make_chunked_file(file_bytes)
    file_hash = chunked_file.address()

    # Segment to prove
    last_segment_index = (len(file_bytes) - 1) // 32

    def test_get_file_hash(segment_index):
        proof_chunks = file_inclusion_proof_bottom_up(chunked_file, segment_index)
        prove_segment = file_bytes[segment_index * SEGMENT_SIZE : segment_index * SEGMENT_SIZE + SEGMENT_SIZE]
        # Padding
        prove_segment += bytearray(SEGMENT_SIZE - len(prove_segment))

        # Check the last segment has the correct span value.
        file_size_from_proof = get_span_value(proof_chunks[-1].span)
        assert file_size_from_proof == len(file_bytes)

        return file_address_from_inclusion_proof(proof_chunks, prove_segment, segment_index)

    # Edge case
    hash1 = test_get_file_hash(last_segment_index)
    assert hash1 == file_hash
    hash2 = test_get_file_hash(1000)
    assert hash2 == file_hash
    with pytest.raises(Exception, match=r"^The given segment index"):
        test_get_file_hash(last_segment_index + 1)


def test_collect_required_segments_for_inclusion_proof_3():
    # the file's byte counts will cause carrier chunk in the intermediate BMT level
    # 128 * 4096 * 128 = 67108864 <- left tree is saturated on bmt level 1
    # 67108864 + 2 * 4096 = 67117056 <- add two full chunks at the end thereby
    # the zero level won't have carrier chunk, but its parent will be that.
    with open(Path(__file__).parent / ".." / "files" / "carrier-chunk-blob-2", "rb") as f:
        carrier_chunk_file_bytes_2 = f.read()
    assert len(carrier_chunk_file_bytes_2) == 67117056

    file_bytes = carrier_chunk_file_bytes_2
    chunked_file = make_chunked_file(file_bytes)
    file_hash = chunked_file.address()
    # segment to prove
    last_segment_index = (len(file_bytes) - 1) // 32

    def test_get_file_hash(segment_index):
        proof_chunks = file_inclusion_proof_bottom_up(chunked_file, segment_index)
        prove_segment = file_bytes[segment_index * SEGMENT_SIZE : (segment_index * SEGMENT_SIZE) + SEGMENT_SIZE]
        # padding
        prove_segment = prove_segment.ljust(SEGMENT_SIZE, b"\0")

        # check the last segment has the correct span value.
        file_size_from_proof = get_span_value(proof_chunks[-1].span)
        assert file_size_from_proof == len(file_bytes)

        return file_address_from_inclusion_proof(proof_chunks, prove_segment, segment_index)

    # edge case
    hash1 = test_get_file_hash(last_segment_index)
    assert hash1 == file_hash
    hash2 = test_get_file_hash(1000)
    assert hash2 == file_hash
    with pytest.raises(Exception, match=r"^The given segment index"):
        test_get_file_hash(last_segment_index + 1)


def test_calculate_address_of_empty_bytes():
    # Create empty bytes
    data = bytes([])
    chunked_file = make_chunked_file(data)
    bmt = chunked_file.bmt()

    assert len(bmt) == 1
    assert len(bmt[0]) == 1

    expected_address = "b34ca8c22b9e982354f9c7f50b470d66db428d880c8a904d5fe4ec9713171526"
    assert bytes_to_hex(chunked_file.address(), 64) == expected_address  # type: ignore
