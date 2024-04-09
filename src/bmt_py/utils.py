from typing import Any, Generic, Optional, TypeVar, Union

from eth_utils import keccak, to_hex
from pydantic import BaseModel, ConfigDict
from typing_extensions import TypeGuard

Min = TypeVar("Min", bound=int)
Max = TypeVar("Max", bound=int)


class FlexBytes(BaseModel, Generic[Min, Max]):
    """
    Helper type for dealing with flexible sized byte arrays.

    The actual min and and max values are not stored in runtime, they
    are only there to differentiate the type from the Uint8Array at
    compile time.

    Args:
        Min (int): The minimum length of the byte array.
        Max (int): The maximum length of the byte array.

    Raises:
        ValueError: If the length of the byte array is not within the specified range.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    min_length: Min
    max_length: Max


def keccak256_hash(*messages: Union[bytes, bytearray]) -> bytes:
    """
    Helper function for calculating the keccak256 hash with

    Args:
        messages: Any number of messages (bytes, byte arrays)
    Returns:
        bytes
    """
    combined = bytearray()
    for message in messages:
        if not isinstance(message, bytearray) and not isinstance(message, bytes):
            msg = f"Input should be either a string, bytes or bytearray: got {type(message)}."
            raise TypeError(msg)
        combined += message

    return keccak(combined)


def serialize_bytes(*arrays: bytes) -> bytes:
    """
    Serialises a sequence of byte arrays into a single byte array.

    Args:
        *arrays (bytes): The sequence of byte arrays to serialize.

    Returns:
        ByteString: The serialized byte array.
    """
    return b"".join(arrays)


def is_flex_bytes(b: Any, flex_bytes: FlexBytes) -> TypeGuard[bytes]:
    """Type guard for the `FlexBytes` type.

    Args:
            b: The value to check.
            flex_bytes: A `FlexBytes` object.

    Returns:
            True if the value is a byte array within the specified length range, False otherwise.
    """

    return isinstance(b, bytes) and flex_bytes.min_length <= len(b) <= flex_bytes.max_length


def bytes_to_hex(inp: Union[bytes, str, bytearray], length: Optional[int] = None) -> str:
    """Converts a byte array to a hexadecimal string.

    Args:
        inp: The byte array to convert.
        length: The length of the resulting hex string in bytes.

    Returns:
        A hexadecimal string representing the byte array.

    Raises:
        ValueError: If the length of the resulting hex string does not match the specified length.
    """
    # * Convert byte array to hexadecimal
    if isinstance(inp, bytes):
        hex_string = to_hex(inp)
    elif isinstance(inp, str):
        hex_string = to_hex(inp.encode())
    elif isinstance(inp, bytearray):
        hex_string = to_hex(inp)
    else:
        msg = "Invalid input type"
        raise ValueError(msg)

    if hex_string.startswith("0x"):
        hex_string = hex_string[2:]  # type: ignore

    if length is not None and len(hex_string) != length:
        msg = f"Length mismatch for valid hex string. Expected length {length}: {hex_string}"
        raise ValueError(msg)

    return hex_string


def bytes_equal(a: bytes, b: bytes) -> bool:
    """Returns True if the two byte arrays are equal, False otherwise.

    Args:
        a: The first byte array to compare.
        b: The second byte array to compare.

    Returns:
        True if the two byte arrays are equal, False otherwise.
    """

    if len(a) != len(b):
        return False

    return all(a[i] == b[i] for i in range(len(a)))


def assert_flex_bytes(b: Any, min_length: int, max_length: int) -> bool:
    """Asserts that `b` is a valid FlexBytes with minimum length `min_length` and maximum length `max_length`.

    Args:
        b (Any): The value to check.
        min_length (int): The minimum length.
        max_length (int): The maximum length.
    Returns:
        boolean: True if `b` is a valid FlexBytes
    Raises:
        TypeError: If `b` is not a valid FlexBytes.
    """
    flex_bytes: FlexBytes = FlexBytes(min_length=min_length, max_length=max_length)

    if not is_flex_bytes(b, flex_bytes):
        return False
    return True
