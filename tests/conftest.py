# from bee_py.bee_debug import BeeDebug
# from bee_py.types.type import PostageBatch
from pytest import fixture


@fixture
def payload() -> bytes:
    return bytes([1, 2, 3])
