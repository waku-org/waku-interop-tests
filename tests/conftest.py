# -*- coding: utf-8 -*-
import glob
import logging
import os
import pytest
from datetime import datetime
from uuid import uuid4
from src.libs.common import attach_allure_file
import src.env_vars as env_vars
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


@pytest.fixture(scope="session", autouse=True)
def set_allure_env_variables():
    yield
    if os.path.isdir("allure-results") and not os.path.isfile(os.path.join("allure-results", "environment.properties")):
        with open(os.path.join("allure-results", "environment.properties"), "w") as outfile:
            for attribute_name in dir(env_vars):
                if attribute_name.isupper():
                    attribute_value = getattr(env_vars, attribute_name)
                    outfile.write(f"{attribute_name}={attribute_value}\n")


@pytest.fixture(scope="function", autouse=True)
def test_id(request):
    # setting up an unique test id to be used where needed
    request.cls.test_id = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}__{str(uuid4())}"


@pytest.fixture(scope="function", autouse=True)
def test_setup(request, test_id):
    logger.debug("Running test: %s with id: %s", request.node.name, request.cls.test_id)


@pytest.fixture(scope="function", autouse=True)
def attach_logs_on_fail(request):
    yield
    if request.node.rep_call.failed:
        logger.debug("Test failed, attempting to attach logs to the allure reports")
        for file in glob.glob(os.path.join(env_vars.LOG_DIR, request.cls.test_id + "*")):
            attach_allure_file(file)


@pytest.fixture(scope="function", autouse=True)
def close_open_nodes():
    DS.waku_nodes = []
    yield
    for node in DS.waku_nodes:
        node.stop()
