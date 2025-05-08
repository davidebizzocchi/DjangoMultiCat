# Agent Management API

> Create and manage AI personalities

These endpoints allow you to create and manage different AI personalities (agents) that can be used in conversations.

## Available Endpoints

| Method | Endpoint | Purpose |
|:------:|----------|---------|
| `GET` | `/agents` | List all available agents |
| `GET` | `/agents/{agent_id}` | Get details about an agent |
| `POST` | `/agents` | Create a new agent |
| `PATCH` | `/agents/{agent_id}` | Update an existing agent |
| `DELETE` | `/agents/{agent_id}` | Delete an agent |

## Usage Examples

### Creating an Agent

```python
import requests

response = requests.post(
    "http://localhost:1865/agents",
    json={
        "name": "Customer Service",
        "instructions": "You are a helpful customer service representative who specializes in solving product issues.",
        "metadata": {"department": "support"}
    },
    headers={"user_id": "your_user_id"}
)

agent_id = response.json()["agent"]["id"]
```

### Listing All Agents

```python
response = requests.get(
    "http://localhost:1865/agents",
    headers={"user_id": "your_user_id"}
)

agents = response.json()["agents"]
for agent in agents:
    print(f"{agent['name']} (ID: {agent['id']})")
```

### Getting Agent Details

```python
agent_id = "abc123"
response = requests.get(
    f"http://localhost:1865/agents/{agent_id}",
    headers={"user_id": "your_user_id"}
)

agent = response.json()["agent"]
print(f"Name: {agent['name']}")
print(f"Instructions: {agent['instructions']}")
```

### Updating an Agent

```python
agent_id = "abc123"
response = requests.patch(
    f"http://localhost:1865/agents/{agent_id}",
    json={
        "name": "Premium Support",
        "instructions": "You are a premium support specialist who provides exceptional assistance."
    },
    headers={"user_id": "your_user_id"}
)
```

### Deleting an Agent

```python
agent_id = "abc123"
response = requests.delete(
    f"http://localhost:1865/agents/{agent_id}",
    headers={"user_id": "your_user_id"}
)
```

### Using an Agent in a Chat

```python
response = requests.post(
    "http://localhost:1865/chat/completions",
    json={
        "message": "I need help with my account",
        "chat_id": "support_session",
        "agent_id": agent_id
    },
    headers={"user_id": "your_user_id"}
)
```

## Common Use Cases

- **Create specialized assistants**: Support agents, tutors, creative writers
- **Switch personalities**: Use different agents for different purposes
- **Build personality library**: Maintain a collection of useful agent profiles
