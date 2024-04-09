import pytest
from bmt_py import (
    bytes_to_hex,
    keccak256_hash,
    make_chunk,
    make_span,
    root_hash_from_inclusion_proof,
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


def test_if_BMTtree_is_in_line_with_chunk_object_calculation(payload):  # noqa: N802
    chunk = make_chunk(payload)
    tree = chunk.bmt()

    assert len(tree) == 8

    root_hash = tree[len(tree) - 1]

    assert keccak256_hash(chunk.span(), root_hash) == chunk.address()


def test_should_retrieve_the_required_segment_pairs_for_inclusion_proof(payload, segment_size):
    chunk = make_chunk(payload)
    tree = chunk.bmt()
    bmt_hash_of_payload = chunk.address()
    assert len(tree) == 8

    def test_get_root_hash(segment_index: int, segment_size: int = segment_size) -> bytes:
        inclusion_proof_segments = chunk.inclusion_proof(segment_index)
        root_hash = root_hash_from_inclusion_proof(
            inclusion_proof_segments,
            chunk.data()[segment_index * segment_size : segment_index * segment_size + segment_size],
            segment_index,
        )
        return root_hash

    root_hash1 = test_get_root_hash(0)
    assert keccak256_hash(make_span(len(payload)), root_hash1) == bmt_hash_of_payload
    root_hash2 = test_get_root_hash(101)
    assert root_hash2 == root_hash1
    root_hash3 = test_get_root_hash(127)
    assert root_hash3 == root_hash1

    with pytest.raises(ValueError):
        test_get_root_hash(128)


@pytest.mark.parametrize(
    "position, expected_segments",
    [
        (
            0,
            [
                "0000000000000000000000000000000000000000000000000000000000000000",
                "ad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5",
                "b4c11951957c6f8f642c4af61cd6b24640fec6dc7fc607ee8206a99e92410d30",
                "21ddb9a356815c3fac1026b6dec5df3124afbadb485c9ba5a3e3398a04b7ba85",
                "e58769b32a1beaf1ea27375a44095a0d1fb664ce2dd358e7fcbfb78c26a19344",
                "0eb01ebfc9ed27500cd4dfc979272d1f0913cc9f66540d7e8005811109e1cf2d",
                "887c22bd8750d34016ac3c66b5ff102dacdd73f6b014e710b51e8022af9a1968",
            ],
        ),
        (
            127,
            [
                "0000000000000000000000000000000000000000000000000000000000000000",
                "ad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5",
                "b4c11951957c6f8f642c4af61cd6b24640fec6dc7fc607ee8206a99e92410d30",
                "21ddb9a356815c3fac1026b6dec5df3124afbadb485c9ba5a3e3398a04b7ba85",
                "e58769b32a1beaf1ea27375a44095a0d1fb664ce2dd358e7fcbfb78c26a19344",
                "0eb01ebfc9ed27500cd4dfc979272d1f0913cc9f66540d7e8005811109e1cf2d",
                "745bae095b6ff5416b4a351a167f731db6d6f5924f30cd88d48e74261795d27b",
            ],
        ),
        (
            64,
            [
                "0000000000000000000000000000000000000000000000000000000000000000",
                "ad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5",
                "b4c11951957c6f8f642c4af61cd6b24640fec6dc7fc607ee8206a99e92410d30",
                "21ddb9a356815c3fac1026b6dec5df3124afbadb485c9ba5a3e3398a04b7ba85",
                "e58769b32a1beaf1ea27375a44095a0d1fb664ce2dd358e7fcbfb78c26a19344",
                "0eb01ebfc9ed27500cd4dfc979272d1f0913cc9f66540d7e8005811109e1cf2d",
                "745bae095b6ff5416b4a351a167f731db6d6f5924f30cd88d48e74261795d27b",
            ],
        ),
    ],
)
def test_inclusion_proof(position, expected_segments):
    data = bytes("hello world", "utf-8")
    chunk = make_chunk(data)

    inclusion_proof_segments = [bytes_to_hex(v, 64) for v in chunk.inclusion_proof(position)]
    assert inclusion_proof_segments == expected_segments


def test_address_calculation_of_empty_bytes():
    data = bytes([])
    chunk = make_chunk(data)

    assert bytes_to_hex(chunk.address(), 64) == "b34ca8c22b9e982354f9c7f50b470d66db428d880c8a904d5fe4ec9713171526"
