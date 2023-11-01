# -*- coding: utf-8 -*-
import logging
import pytest
from src.data_storage import DS

logger = logging.getLogger(__name__)


# See https://docs.pytest.org/en/latest/example/simple.html#making-test-result-information-available-in-fixtures
@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        setattr(item, "rep_call", rep)
        return rep
    return None


@pytest.fixture(scope="function", autouse=True)
def test_setup(request):
    logger.debug("Running test: %s", request.node.name)


@pytest.fixture(scope="function", autouse=True)
def close_open_nodes():
    DS.waku_nodes = []
    yield
    for node in DS.waku_nodes:
        node.stop()
