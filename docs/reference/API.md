# API 

## Types

| | | 
|----------------------------------|-----------------------------------|
| chunk                            | interface of the helper object for performing BMT actions on chunk data |
| payload                          | the passed byte payload with which the object was initialized. |
| max_payload_length               | the maximum payload byte length in the chunk. It is 4096 by default. |
| span_length                      | the reserved byte length for span serialisation. By default it is 8 bytes. |
| data()                           | gives back the chunk's data that is exactly `maxPayloadLength` long |
| span()                           | serialized span value of chunk |
| address()                        | gives back the calculated chunk address of the data |
| inclusion_proof(segment_index)  | gives back the inclusion proof segments for proofing the segment under the given index. |
| bmt()                            | gives back the Binary Merkle Tree of the chunk data |
| chunked_file                     | interface of the helper object for performing BMT actions on file data |
| payload                          | the passed byte payload with which the object was initialized. |
| leaf_chunks()                    | data chunks of the file data |
| root_chunk()                     | topmost chunk in the file BMT |
| address()                        | gives back the calculated chunk address of file data |
| span()                           | serialized span value of the file |
| bmt()                            | gives back the Binary Merkle Tree of the file data |
| chunk_inclusion_proof            | groups chunk inclusion proof segments and span value of a chunk |
| chunk_address                    | chunk address resulted from BMT hashing of data. It is used also for FileAddress |
| span                             | span value in byte format. Indicates how much data subsumed under the Chunk/File |

## Functions

| | |
|----------------------------------|-----------------------------------|
| make_chunked_file                | makes `Chunk` helper object for performing BMT actions on file data |
| make_chunk                       | makes `Chunk` helper object for performing BMT actions on chunk data |
| make_span                        | make serialized `Span` byte array that indicates how much data subsumed under the Chunk/File |
| get_span_value                   | deserialized data into `number` carrier by `Span` |
| root_hash_from_inclusion_proof   | calculate the BMT root hash from the provided inclusion proof segments and its corresponding segment index |
| get_bmt_index_of_segment         | get the chunk's position of a given payload segment index in the BMT tree |
| file_inclusion_proof_bottom_up   | gives back required sister segments of a given payload segment index for inclusion proof |
| file_address_from_inclusion_proof | gives back the file address that is calculated with only the inclusion proof segments and the corresponding proved segment and its position. |
| 

## Others

| | |
|----------------------------------|-----------------------------------|
| utils                            | mainly bytes related utility functions |
