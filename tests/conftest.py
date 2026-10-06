import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import analysis  # noqa: E402
import business_case  # noqa: E402
import experiment  # noqa: E402


@pytest.fixture(scope="session")
def a():
    return analysis.run()


@pytest.fixture(scope="session")
def bc():
    return business_case.run()


@pytest.fixture(scope="session")
def ex():
    return experiment.run()
