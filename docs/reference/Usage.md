### BMT Root Hash Calculation Python Module Test Cases

---

#### Overview

This document provides a summary of the test cases for the BMT Root Hash Calculation Python Module. Each test case validates a specific functionality or feature of the module.

---

#### Test Chunking with Payload Lesser Than 4KB

- **Description**: Validates the chunking process with payload data less than 4KB.
- **Test Function**: `test_chunked_file_with_lesser_than_4KB_of_data`
- **Expected Outcome**: The payload is correctly chunked, and the span values are as expected.

##### Usage Example:
```py
payload = bytes([1, 2, 3])
chunked_file = make_chunked_file(payload)

print(len(chunked_file.leaf_chunks()))
# 1
only_chunk = chunked_file.leaf_chunks()[0]
only_chunk.span() == chunked_file.span()
# True
only_chunk.address() == chunked_file.address()
# True
```

#### Test Chunking with Payload Greater Than 4KB
- **Description:** Validates the chunking process with payload data greater than 4KB.
- **Test Function**: `test_chunked_file_with_greater_than_4KB_of_data`
- **Expected Outcome**: The payload is correctly chunked, and the BMT root hash is calculated accurately.

##### Usage Example:
```py
from bmt_py import make_chunked_file, get_span_value, bytes_to_hex
with open("The-Book-of-Swarm.pdf", "rb") as f:
    file_bytes = f.read()
chunked_file = make_chunked_file(file_bytes)

print(get_span_value(chunked_file.span()))
# 15726634
tree = chunked_file.bmt()
print(len(tree))
# 3
print(len(tree[2])) # last level only contains the root_chunk
# 1

root_chunk = tree[2][0]
second_level_first_chunk = tree[1][0]  # first intermediate chunk on the first intermediate chunk level
root_chunk.payload[:32] == second_level_first_chunk.address()
# True
print(len(second_level_first_chunk.payload))
# 4096

print(bytes_to_hex(chunked_file.address(), 64))
# b8d17f296190ccc09a2c36b7a59d0f23c4479a3958c3bb02dc669466ec919c5d
```

### Test files
These test cases are testing the functionality of collecting required segments for inclusion proof in a chunked file system, particularly focusing on different scenarios and edge cases.

1. **`test_collect_required_segments_for_inclusion_proof`**: 
   - This test checks whether the function `file_inclusion_proof_bottom_up()` correctly collects the required segments for inclusion proof.
   - It starts by generating a chunked file from the `carrier_chunk_file_bytes`.
   - Then, it determines the `segment_index` to be proved based on the length of the file.
   - It collects the required segments using `file_inclusion_proof_bottom_up()` and verifies that the number of segments collected is correct.
   - It defines an inner function `test_get_file_hash(segment_index)` to perform further checks. This function collects the inclusion proof chunks, prepares the segment to be proved, checks the correctness of the span value of the last segment, and finally computes the file hash from the inclusion proof.
   - It verifies the correctness of the computed hash against the expected file hash for both the given segment index and an arbitrary segment index (1000 in this case).

```py
def test_collect_required_segments_for_inclusion_proof():
    with open("carrier-chunk-blob", "rb") as f:
        file_bytes = f.read()
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
```



2. **`test_collect_required_segments_for_inclusion_proof_2`**:
   - This test is similar to the previous one but focuses on different scenarios.
   - It starts by generating a chunked file from `bos_bytes`.
   - It calculates the `last_segment_index` based on the length of the file.
   - It defines an inner function `test_get_file_hash(segment_index)` to perform similar checks as the previous test.
   - It verifies the correctness of the computed hash against the expected file hash for both the last segment index and an arbitrary segment index (1000 in this case).
   - Additionally, it checks whether the function raises an exception when given a segment index beyond the last segment.

```py
def test_collect_required_segments_for_inclusion_proof_2(bos_bytes):
    with open("The-Book-of-Swarm.pdf", "rb") as f:
        bos_bytes = f.read()
    chunked_file = make_chunked_file(bos_bytes)
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
```

3. **`test_collect_required_segments_for_inclusion_proof_3`**:
   - This test focuses on an edge case where the file's byte counts lead to a carrier chunk in the intermediate BMT level.
   - It loads the data from a specific file (`carrier-chunk-blob-2`) and ensures its length is as expected.
   - It generates a chunked file from this data and calculates the expected file hash.
   - It defines an inner function `test_get_file_hash(segment_index)` to perform similar checks as the previous tests.
   - It verifies the correctness of the computed hash against the expected file hash for both the last segment index and an arbitrary segment index (1000 in this case).
   - Additionally, it checks whether the function raises an exception when given a segment index beyond the last segment.

```py
def test_collect_required_segments_for_inclusion_proof_3():
    # the file's byte counts will cause carrier chunk in the intermediate BMT level
    # 128 * 4096 * 128 = 67108864 <- left tree is saturated on bmt level 1
    # 67108864 + 2 * 4096 = 67117056 <- add two full chunks at the end thereby
    # the zero level won't have carrier chunk, but its parent will be that.
    with open("carrier-chunk-blob-2", "rb") as f:
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
```