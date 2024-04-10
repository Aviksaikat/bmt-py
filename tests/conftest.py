# from bee_py.types.type import PostageBatch
from pathlib import Path

import pytest
from pytest import fixture

SEGMENT_SIZE = 32
PROJECT_PATH = Path(__file__).parent
ENV_FILE = PROJECT_PATH / "../.env"


@fixture
def payload() -> bytes:
    return bytes([1, 2, 3])


@fixture
def segment_size() -> int:
    return SEGMENT_SIZE


@pytest.fixture(scope="module", autouse=True)
def bos_bytes():
    bos_bytes = None
    with open(Path(__file__).parent / "files" / "The-Book-of-Swarm.pdf", "rb") as f:
        bos_bytes = f.read()
    return bos_bytes


@pytest.fixture(scope="module", autouse=True)
def carrier_chunk_file_bytes():
    carrier_chunk_file_bytes = None
    with open(Path(__file__).parent / "files" / "carrier-chunk-blob", "rb") as f:
        carrier_chunk_file_bytes = f.read()

    return carrier_chunk_file_bytes


##* For integration tests

# @pytest.fixture(scope="session", autouse=True)
# def bee_api_url():
#     BEE_API_URL = ""
#     if os.path.isfile(ENV_FILE):
#         with open(ENV_FILE) as f:
#             data = json.loads(f.read())
#         if data["BEE_API_URL"]:
#             BEE_API_URL = data["BEE_API_URL"]
#     else:
#         BEE_API_URL = "http://localhost:1633"

#     return BEE_API_URL


# @pytest.fixture(scope="session", autouse=True)
# def bee_class(bee_api_url):
#     return Bee(bee_api_url)


# @pytest.fixture(scope="session", autouse=True)
# def stamp():
#     if os.path.isfile(ENV_FILE):
#         with open(ENV_FILE) as f:
#             data = json.loads(f.read())
#         if data["BEE_POSTAGE"]:
#             BEE_POSTAGE = data["BEE_POSTAGE"]
#             return BEE_POSTAGE
#     msg = "BEE_POSTAGE system environment variable is not defined"
#     raise Exception(msg)
