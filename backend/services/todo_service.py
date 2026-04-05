"""TODO service."""

import uuid
from datetime import UTC, datetime

from clients.dynamodb import get_dynamodb_resource, get_settings


def list_todos(user_id: str) -> list[dict]:
    """List all todos for a user."""
    settings = get_settings()
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(settings.todos_table_name)

    response = table.query(
        KeyConditionExpression="pk = :pk",
        ExpressionAttributeValues={":pk": f"USER#{user_id}"},
    )
    return [
        {
            "todo_id": item["todo_id"],
            "title": item["title"],
            "completed": item["completed"],
            "created_at": item["created_at"],
        }
        for item in response["Items"]
    ]


def create_todo(user_id: str, title: str) -> dict:
    """Create a new todo."""
    settings = get_settings()
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(settings.todos_table_name)

    todo_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    item = {
        "pk": f"USER#{user_id}",
        "sk": f"TODO#{todo_id}",
        "todo_id": todo_id,
        "title": title,
        "completed": False,
        "created_at": now,
    }
    table.put_item(Item=item)
    return {"todo_id": todo_id, "title": title, "completed": False, "created_at": now}


def update_todo(user_id: str, todo_id: str, title: str | None = None, completed: bool | None = None) -> dict | None:
    """Update a todo. Returns updated todo or None if not found."""
    settings = get_settings()
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(settings.todos_table_name)

    key = {"pk": f"USER#{user_id}", "sk": f"TODO#{todo_id}"}

    # Check existence
    response = table.get_item(Key=key)
    item = response.get("Item")
    if not item:
        return None

    # Build update expression
    update_parts = []
    attr_values = {}
    if title is not None:
        update_parts.append("title = :title")
        attr_values[":title"] = title
    if completed is not None:
        update_parts.append("completed = :completed")
        attr_values[":completed"] = completed

    if not update_parts:
        return {
            "todo_id": item["todo_id"],
            "title": item["title"],
            "completed": item["completed"],
            "created_at": item["created_at"],
        }

    table.update_item(
        Key=key,
        UpdateExpression="SET " + ", ".join(update_parts),
        ExpressionAttributeValues=attr_values,
    )

    # Return updated item
    response = table.get_item(Key=key)
    updated = response["Item"]
    return {
        "todo_id": updated["todo_id"],
        "title": updated["title"],
        "completed": updated["completed"],
        "created_at": updated["created_at"],
    }


def delete_todo(user_id: str, todo_id: str) -> bool:
    """Delete a todo. Returns True if deleted, False if not found."""
    settings = get_settings()
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(settings.todos_table_name)

    key = {"pk": f"USER#{user_id}", "sk": f"TODO#{todo_id}"}

    response = table.get_item(Key=key)
    if not response.get("Item"):
        return False

    table.delete_item(Key=key)
    return True
