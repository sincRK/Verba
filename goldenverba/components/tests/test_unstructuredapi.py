import base64
from pathlib import Path

import pytest

from goldenverba.components.reader.document import Document
from goldenverba.components.reader.unstructuredapi import UnstructuredAPI


@pytest.fixture
def byte_data():
    return [base64.b64encode(b"Test text content.").decode("utf-8")]


@pytest.fixture
def file_names():
    # Get the absolute directory path of this test file.
    test_dir = Path(__file__).parent
    # Build an absolute path for the test file.
    return [str(test_dir / "./data/test.txt")]


@pytest.fixture
def content_data():
    return ["Test text content."]


def test_unstructured_api_reader_load_from_bytes(byte_data, file_names):
    reader = UnstructuredAPI()
    documents = reader.load(bytes=byte_data, fileNames=file_names)
    assert isinstance(documents, list)
    assert len(documents) == 1
    assert isinstance(documents[0], Document)
    assert documents[0].text == "Test text content."


def test_unstructured_api_reader_load_from_paths(file_names):
    reader = UnstructuredAPI()
    documents = reader.load(paths=file_names)
    assert isinstance(documents, list)
    assert len(documents) == 1
    assert isinstance(documents[0], Document)
    assert documents[0].text == "This is a test."


def test_unstructured_api_reader_load_from_contents(content_data, file_names):
    reader = UnstructuredAPI()
    documents = reader.load(contents=content_data, fileNames=file_names)
    assert isinstance(documents, list)
    assert len(documents) == 1
    assert isinstance(documents[0], Document)
    assert documents[0].text == "Test text content."
