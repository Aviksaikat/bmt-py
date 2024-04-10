# # from bee_py.bee import Bee
# from pathlib import Path

# from bee_py.types.type import SPAN_SIZE
# from bmt_py import bytes_to_hex, make_chunked_file
# from bmt_py.chunk import DEFAULT_MAX_PAYLOAD_SIZE

## *Need to test against a bee Node

# def test_produce_same_chunk_like_bee_for_data_less_than_4kb(bee_class, stamp):
#     # Use pathlib to read the file
#     file_path = Path(__file__).parent / ".." / "files" / "text.txt"
#     file_bytes = file_path.read_bytes()

#     chunked_file = make_chunked_file(file_bytes)
#     result = bee_class.upload_data(stamp, file_bytes)
#     reference = result.reference

#     expected_address = bytes_to_hex(chunked_file.address(), 64)  # type: ignore
#     assert expected_address == reference


# def test_produce_same_bmt_tree_like_bee_for_data_greater_than_4kb(bee_class, stamp):
#     file_path = Path(__file__).parent / ".." / "files" / "The-Book-of-Swarm.pdf"
#     file_bytes = file_path.read_bytes()

#     chunked_file = make_chunked_file(file_bytes)
#     result = bee_class.upload_data(stamp, file_bytes)
#     reference = result.reference

#     span_and_chunk_payload_length = DEFAULT_MAX_PAYLOAD_SIZE + SPAN_SIZE
#     bee_root_chunk = bee_class.download_chunk(reference)
#     assert len(bee_root_chunk) == 968
#     bee_2nd_layer_1st_chunk_address = bee_root_chunk[8:40]
#     bee_2nd_layer_1st_chunk = bee_class.download_chunk(
#         bytes_to_hex(bee_2nd_layer_1st_chunk_address, 64)
#     )
#     assert len(bee_2nd_layer_1st_chunk) == span_and_chunk_payload_length
#     bee_leaf_layer_1st_chunk = bee_class.download_chunk(
#         bytes_to_hex(bee_2nd_layer_1st_chunk[8:40], 64)
#     )
#     assert len(bee_leaf_layer_1st_chunk) == span_and_chunk_payload_length

#     tree = chunked_file.bmt()
#     assert tree[0][0].payload == bee_leaf_layer_1st_chunk[8:]

#     assert tree[1][0].payload == bee_2nd_layer_1st_chunk[8:]
#     assert tree[1][0].span() == bee_2nd_layer_1st_chunk[:8]
#     assert tree[1][0].address() == bee_2nd_layer_1st_chunk_address
#     assert bytes_to_hex(tree[2][0].address(), 64) == reference
