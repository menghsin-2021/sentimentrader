import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--dbname",
        action="store"
    )

@pytest.fixture()
def db_env(request):
    return request.config.getoption("--dbname")