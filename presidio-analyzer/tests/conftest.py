import shutil
from pathlib import Path

import pytest
import spacy

from presidio_analyzer import EntityRecognizer
from presidio_analyzer import RecognizerRegistry
from presidio_analyzer.nlp_engine import NLP_ENGINES
from presidio_analyzer.predefined_recognizers import NLP_RECOGNIZERS
from tests.mocks import RecognizerRegistryMock


def pytest_addoption(parser):
    parser.addoption(
        "--runfast", action="store_true", default=False, help="run fast tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")
    config.addinivalue_line(
        "markers", "skip_engine(nlp_engine): skip test for given nlp engine"
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runfast"):
        # --runfast given in cli: skip slow tests
        skip_slow = pytest.mark.skip(reason="remove --runfast option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)


@pytest.fixture(scope="session")
def nlp_engines(request):
    available_engines = {}
    for name, engine_cls in NLP_ENGINES.items():
        if name == "spacy" and not request.config.getoption("--runfast"):
            available_engines[f"{name}_en"] = engine_cls({"en": "en_core_web_lg"})
        else:
            available_engines[f"{name}_en"] = engine_cls()

    return available_engines


@pytest.fixture(autouse=True)
def skip_by_engine(request, nlp_engines):
    marker = request.node.get_closest_marker("skip_engine")
    if marker:
        marker_arg = marker.args[0]
        if marker_arg not in nlp_engines:
            pytest.skip(f"skipped on this engine: {marker_arg}")


@pytest.fixture(scope="session")
def nlp_recognizers():
    return {name: rec_cls() for name, rec_cls in NLP_RECOGNIZERS.items()}


@pytest.fixture(scope="session")
def ner_strength():
    return 0.85


@pytest.fixture(scope="session")
def max_score():
    return EntityRecognizer.MAX_SCORE


@pytest.fixture(scope="module")
def loaded_registry():
    return RecognizerRegistry()


@pytest.fixture(scope="module")
def mock_registry():
    return RecognizerRegistryMock()


@pytest.fixture(scope="session")
def mock_he_model():
    """
    Create an empty Hebrew spaCy pipeline and save it to disk.

    So that it could be loaded using spacy.load()
    """
    he = spacy.blank("he")
    he.to_disk("he_test")


@pytest.fixture(scope="session")
def mock_bn_model():
    """
    Create an empty Bengali spaCy pipeline and save it to disk.

    So that it could be loaded using spacy.load()
    """
    bn = spacy.blank("bn")
    bn.to_disk("bn_test")


def pytest_sessionfinish():
    """Remove files created during mock spaCy models creation."""
    he_test_model_path = Path(Path(__file__).parent.parent, "he_test")
    if he_test_model_path.exists():
        try:
            shutil.rmtree(he_test_model_path)
        except OSError as e:
            print("Failed to remove file: %s - %s." % (e.filename, e.strerror))

    bn_test_model_path = Path(Path(__file__).parent.parent, "bn_test")
    if bn_test_model_path.exists():
        try:
            shutil.rmtree(bn_test_model_path)
        except OSError as e:
            print("Failed to remove file: %s - %s." % (e.filename, e.strerror))
