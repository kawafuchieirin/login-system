"""Test fixtures."""

import os
from unittest.mock import patch

import boto3
import pytest
from moto import mock_aws

# Set test environment variables before importing app
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["USERS_TABLE_NAME"] = "test-users"
os.environ["TODOS_TABLE_NAME"] = "test-todos"
os.environ["DEBUG"] = "true"


@pytest.fixture(autouse=True)
def _reset_settings():
    """Clear cached settings between tests."""
    from clients.dynamodb import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _create_tables(dynamodb):
    """Create DynamoDB tables for testing."""
    dynamodb.create_table(
        TableName="test-users",
        AttributeDefinitions=[
            {"AttributeName": "pk", "AttributeType": "S"},
            {"AttributeName": "email", "AttributeType": "S"},
        ],
        KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"}],
        BillingMode="PAY_PER_REQUEST",
        GlobalSecondaryIndexes=[
            {
                "IndexName": "email-index",
                "KeySchema": [{"AttributeName": "email", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
    )
    dynamodb.create_table(
        TableName="test-todos",
        AttributeDefinitions=[
            {"AttributeName": "pk", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "pk", "KeyType": "HASH"},
            {"AttributeName": "sk", "KeyType": "RANGE"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )


@pytest.fixture()
def client():
    """Create test client with mocked DynamoDB."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "ap-northeast-1"

    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-1")
        _create_tables(dynamodb)

        with patch("clients.dynamodb.get_dynamodb_resource", return_value=dynamodb):
            from fastapi.testclient import TestClient

            from main import app

            yield TestClient(app)


@pytest.fixture()
def auth_headers(client):
    """Register a user and return auth headers."""
    client.post("/api/v1/auth/register", json={"email": "test@example.com", "password": "password123"})
    response = client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "password123"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
