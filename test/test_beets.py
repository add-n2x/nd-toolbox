import pytest

from ndtoolbox.beets import BeetsClient
from ndtoolbox.config import config

config.set_file("test/config/config.yaml")


def test_beets_client():
    """Test Beets client."""
    client = BeetsClient()
    assert client is not None
