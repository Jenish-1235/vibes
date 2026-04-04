"""
Shared pytest fixtures.

AWS calls in unit tests are mocked via moto.
Integration tests require real containers — skip automatically if endpoints not set.
"""
import os
import pytest


@pytest.fixture(autouse=True, scope="session")
def disable_real_aws():
    """Prevent unit tests from accidentally hitting real AWS."""
    os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
    os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
    os.environ.setdefault("AWS_SECURITY_TOKEN", "testing")
    os.environ.setdefault("AWS_SESSION_TOKEN", "testing")
