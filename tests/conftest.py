# from bee_py.bee_debug import BeeDebug
# from bee_py.types.type import PostageBatch
from pytest import fixture

SEGMENT_SIZE = 32


@fixture
def payload() -> bytes:
    return bytes([1, 2, 3])


@fixture
def segment_size() -> int:
    return SEGMENT_SIZE
