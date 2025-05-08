# Collections API

> Manage files and their associations with chats

These endpoints allow you to work with memory collections, particularly managing file metadata and chat associations.

## Available Endpoints

| Method | Endpoint | Purpose |
|:------:|----------|---------|
| `GET` | `/memory/collections/{collection_id}/points` | Get all memory points matching metadata criteria |
| `GET` | `/memory/collections/{collection_id}/points/by_metadata` | Get simplified metadata view of memory points |
| `PATCH` | `/memory/collections/{collection_id}/points/metadata` | Update metadata for memory points |
| `PATCH` | `/memory/collections/{collection_id}/points/edit_chat_ids` | Add or remove chat IDs from memory points |

---

## Endpoints

### Get Memory Points

```http
GET /memory/collections/{collection_id}/points
```

Retrieves memory points matching specific metadata criteria.

#### Query Parameters

- `collection_id` (path): Name of the collection (usually "declarative")
- `metadata` (query): Metadata criteria to match

#### Example

```python
import requests
import json

response = requests.get(
    "http://localhost:1865/memory/collections/declarative/points",
    params={"metadata": json.dumps({"file_id": "invoice_123"})},
    headers={"user_id": "your_user_id"}
)

points = response.json()["points"]
print(f"Found {len(points)} matching memory points")
```

### Get Points Metadata Only

```http
GET /memory/collections/{collection_id}/points/by_metadata
```

Retrieves a simplified view with only metadata from memory points.

#### Example

```python
import requests
import json

response = requests.get(
    "http://localhost:1865/memory/collections/declarative/points/by_metadata",
    params={"metadata": json.dumps({"file_id": "invoice_123"})},
    headers={"user_id": "your_user_id"}
)

for point in response.json()["points"]:
    print(f"Point ID: {point['id']}")
    print(f"Metadata: {point['metadata']}")
```

### Update Points Metadata

```http
PATCH /memory/collections/{collection_id}/points/metadata
```

Updates metadata for points matching specific criteria.

#### Request Body

```json
{
  "search": {"file_id": "invoice_123"},
  "update": {"status": "reviewed", "priority": "high"}
}
```

#### Example

```python
import requests

response = requests.patch(
    "http://localhost:1865/memory/collections/declarative/points/metadata",
    json={
        "search": {"file_id": "invoice_123"},
        "update": {"status": "reviewed", "priority": "high"}
    },
    headers={"user_id": "your_user_id"}
)

print(f"Updated {response.json()['count']} memory points")
```

### Edit Chat Associations

```http
PATCH /memory/collections/{collection_id}/points/edit_chat_ids?mode=add
```

Adds or removes chat IDs from memory points metadata.

#### URL Parameters

- `mode`: Either "add" or "remove"

#### Request Body

```json
{
  "search_metadata": {"file_id": "invoice_123"},
  "chats_id": ["accounting", "finance_review"]
}
```

#### Example: Adding Chat Associations

```python
import requests

# Associate a file with chats
response = requests.patch(
    "http://localhost:1865/memory/collections/declarative/points/edit_chat_ids?mode=add",
    json={
        "search_metadata": {"file_id": "invoice_123"},
        "chats_id": ["accounting", "finance_review"]
    },
    headers={"user_id": "your_user_id"}
)
```

#### Example: Removing Chat Associations

```python
import requests

# Remove a file from chats
response = requests.patch(
    "http://localhost:1865/memory/collections/declarative/points/edit_chat_ids?mode=remove",
    json={
        "search_metadata": {"file_id": "invoice_123"},
        "chats_id": ["accounting"]
    },
    headers={"user_id": "your_user_id"}
)
```

## Common Use Cases

### Managing File Visibility

Control which chats can access specific files:

```python
# Make a contract visible in multiple relevant chats
requests.patch(
    "http://localhost:1865/memory/collections/declarative/points/edit_chat_ids?mode=add",
    json={
        "search_metadata": {"file_id": "contract_2023"},
        "chats_id": ["legal_review", "executive_team"]
    },
    headers={"user_id": "your_user_id"}
)

# Remove access when a project is completed
requests.patch(
    "http://localhost:1865/memory/collections/declarative/points/edit_chat_ids?mode=remove",
    json={
        "search_metadata": {"file_id": "project_specs"},
        "chats_id": ["archived_project"]
    },
    headers={"user_id": "your_user_id"}
)
```

### Updating File Information

Add or update metadata for files:

```python
# Mark documents as reviewed
requests.patch(
    "http://localhost:1865/memory/collections/declarative/points/metadata",
    json={
        "search": {"file_id": "report_q3"},
        "update": {
            "status": "reviewed",
            "reviewer": "Jane Smith",
            "review_date": "2023-10-15"
        }
    },
    headers={"user_id": "your_user_id"}
)
```

### Finding Files by Criteria

Search for files matching specific metadata:

```python
import requests
import json

# Find all files related to a specific project
response = requests.get(
    "http://localhost:1865/memory/collections/declarative/points/by_metadata",
    params={"metadata": json.dumps({"project": "alpha"})},
    headers={"user_id": "your_user_id"}
)

# Get all files accessible in a specific chat
response = requests.get(
    "http://localhost:1865/memory/collections/declarative/points/by_metadata",
    params={"metadata": json.dumps({"chats_id": "team_meeting"})},
    headers={"user_id": "your_user_id"}
)
```

These endpoints provide powerful ways to manage your file metadata and control which chats can access specific knowledge.
