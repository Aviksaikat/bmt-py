from bmt_py import (
    bytes_to_hex,
    make_chunk,
)


def test_initialise_chunk_object(payload):

    expected_span = bytes([3, 0, 0, 0, 0, 0, 0, 0])

    chunk = make_chunk(payload)

    assert chunk.payload == payload
    assert chunk.span() == expected_span
    assert len(chunk.data()) == 4096
    assert len(chunk.address()) == 32


def test_produce_correct_BMT_hash(payload):  # noqa: N802
    expected_hash = "ca6357a08e317d15ec560fef34e4c45f8f19f01c372aa70f1da72bfa7f1a4338"

    chunk = make_chunk(payload)

    result = chunk.address()

    assert bytes_to_hex(result, 64) == expected_hash
