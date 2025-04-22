# Conversation History API

> Manage message histories within chat sessions

These endpoints let you view and manipulate the message history for specific chats.

## Available Endpoints

| Method | Endpoint | Purpose |
|:------:|----------|---------|
| `GET` | `/memory/conversation_history` | Get current chat history |
| `DELETE` | `/memory/conversation_history/{chat_id}` | Clear messages from a chat |
| `POST` | `/memory/conversation_history/{chat_id}` | Add custom messages to history |
| `GET` | `/memory/conversation_history/{chat_id}/length` | Count messages in a chat |

## Viewing Chat History

```python
import requests

# Get current chat's conversation history
response = requests.get(
    "http://localhost:1865/memory/conversation_history",
    headers={"user_id": "your_user_id"}
)

messages = response.json()["history"]
for msg in messages:
    print(f"{msg['who']}: {msg['text']}")
```

## Clearing Chat History

```python
chat_id = "project_chat"
response = requests.delete(
    f"http://localhost:1865/memory/conversation_history/{chat_id}",
    headers={"user_id": "your_user_id"}
)

# Messages are removed but chat context remains
```

## Adding Custom Messages

```python
chat_id = "onboarding"
response = requests.post(
    f"http://localhost:1865/memory/conversation_history/{chat_id}",
    json={
        "message": {
            "text": "Welcome to the system! Let me guide you.",
            "who": "AI",
            "chat_id": chat_id,
            "user_id": "system"
        },
        "index": 0  # Add at the beginning of history
    },
    headers={"user_id": "your_user_id"}
)
```

## Checking History Length

```python
chat_id = "support_ticket"
response = requests.get(
    f"http://localhost:1865/memory/conversation_history/{chat_id}/length",
    headers={"user_id": "your_user_id"}
)

message_count = response.json()["length"]
print(f"This conversation has {message_count} messages")
```

## Common Use Cases

- **Create guided experiences**: Insert AI messages that provide instructions
- **Reset conversations**: Clear history while maintaining context
- **Build conversation templates**: Pre-populate chat histories with useful content
- **Implement tutorials**: Create step-by-step guided interactions
