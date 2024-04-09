from pathlib import Path

import pytest
from bmt_py import (
    file_address_from_inclusion_proof,
    file_inclusion_proof_bottom_up,
    make_chunked_file,
)

# Load the carrier chunk file bytes
carrier_chunk_file_path = Path(__file__).parent / ".." / "files" / "carrier-chunk-blob"
carrier_chunk_file_bytes = bytearray(carrier_chunk_file_path.read_bytes())


@pytest.mark.parametrize(
    "segment_index, byte_offset",
    [
        (0, 0),
        # (1, 0),
        # (len(carrier_chunk_file_bytes) // 32 - 1, 0),
        # (len(carrier_chunk_file_bytes) // 32 - 2, 0),
        # (7, 0),
        # (13, 0),
        # (103, 31),
        # (1000, 10),
    ],
)
def test_alter_one_segment_with_params(segment_index, byte_offset):
    # Create a copy of the carrier chunk file bytes
    carrier_chunk_file_bytes_copy = bytearray(carrier_chunk_file_bytes)

    # Alter one segment
    byte_index = segment_index * 32
    carrier_chunk_file_bytes_copy[byte_index + byte_offset] += 1

    # Create chunked files
    chunk_file1 = make_chunked_file(bytes(carrier_chunk_file_bytes))
    chunk_file2 = make_chunked_file(bytes(carrier_chunk_file_bytes_copy))

    # Get sister segments
    sister_segments1 = file_inclusion_proof_bottom_up(chunk_file1, segment_index)
    sister_segments2 = file_inclusion_proof_bottom_up(chunk_file2, segment_index)

    # Assert that sister segments are the same
    assert sister_segments1 == sister_segments2

    # Sanity checks
    file1_address = chunk_file1.address()
    file2_address = chunk_file2.address()
    assert file1_address != file2_address

    segment1 = carrier_chunk_file_bytes[byte_index : byte_index + 32]
    segment2 = carrier_chunk_file_bytes_copy[byte_index : byte_index + 32]

    # Padding
    segment1 += bytearray(32 - len(segment1))
    segment2 += bytearray(32 - len(segment2))

    assert segment1 != segment2
    assert file_address_from_inclusion_proof(sister_segments1, segment1, segment_index) == file1_address
    assert file_address_from_inclusion_proof(sister_segments2, segment2, segment_index) == file2_address
