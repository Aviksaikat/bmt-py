import struct
from typing import Optional

# * Constants
DEFAULT_SPAN_SIZE = 8
# * We limit the maximum span size in 32 bits to avoid BigInt compatibility issues
MAX_SPAN_LENGTH = 2**32 - 1


def make_span(value: int, length: Optional[int] = DEFAULT_SPAN_SIZE) -> bytes:
    """
    Creates a span for storing the length of a chunk.

    The length is encoded in 64-bit little endian format.

    Args:
        value (int): Value of the span
        length (int): The length of the chunk.

    Returns:
        bytes: The span representing the chunk length.
    """
    if value < 0:
        msg = f"invalid length for span: {value}"
        raise ValueError(msg)

    if value > MAX_SPAN_LENGTH:
        msg = f"invalid length (> {MAX_SPAN_LENGTH}) {value}"
        raise ValueError(msg)

    span = bytearray(length)  # type: ignore
    length_lower_32 = value & 0xFFFFFFFF

    struct.pack_into("<I", span, 0, length_lower_32)  # Pack the lower 32 bits as little endian

    return bytes(span)


def get_span_value(span: bytes) -> int:
    """
    Extract a 32-bit unsigned integer from the span's buffer.

    Args:
        span (bytes): The span containing the data.

    Returns:
        An integer value representing the unsigned 32-bit integer.

    """
    # return struct.unpack("I", span.cast("B", (span.nbytes)))[0]
    return int.from_bytes(span[0:4], byteorder="little", signed=False)
