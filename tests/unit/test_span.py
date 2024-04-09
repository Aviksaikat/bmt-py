import pytest
from bmt_py import get_span_value, make_span
from bmt_py.span import MAX_SPAN_LENGTH


@pytest.mark.parametrize(
    "input_length,expected_length",
    [
        (4096, 4096),
        (MAX_SPAN_LENGTH, MAX_SPAN_LENGTH),
        (1, 1),
    ],
)
def test_serialise_n_deserialise(input_length, expected_length):
    if input_length == 0:
        with pytest.raises(expected_length):
            make_span(input_length)
    chunk_length_bytes = make_span(input_length)
    chunk_length = get_span_value(chunk_length_bytes)

    assert chunk_length == expected_length
