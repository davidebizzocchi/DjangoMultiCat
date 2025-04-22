# Multi-Chat Architecture

> Run independent conversation sessions with Multicat

## What It Does

Multicat lets you run multiple separate conversation contexts with Cheshire Cat, each maintaining its own:

- Message history
- Memory context
- Agent personality

This means you can have parallel conversations that don't interfere with each other.

## Basic Concept

```markdown
┌────────────────────────────────────────┐
│             Cheshire Cat               │
│                                        │
│   ┌─────────┐  ┌─────────┐  ┌─────┐    │
│   │  Chat 1 │  │  Chat 2 │  │ ... │    │
│   │ Context │  │ Context │  │     │    │
│   └─────────┘  └─────────┘  └─────┘    │
└────────────────────────────────────────┘
```

## Using Multiple Chats

To use multiple conversations, simply specify a `chat_id` when sending messages:

```python
work_message = {
    "text": "What are our project deadlines?",
    "chat_id": "work"
}

personal_message = {
    "text": "Any good dinner recipes?",
    "chat_id": "personal"
}
```

Each chat maintains its own conversation **flow, memory, and context**.

## Managing Chat Sessions

View all your active chats:

```python
response = requests.get(
    "http://localhost:1865/memory/working_memories",
    headers={"user_id": "your_user_id"}
)
chat_list = response.json()["working_memories"]
```

Delete a chat when you're done:

```python
requests.delete(
    "http://localhost:1865/memory/working_memories/old_project",
    headers={"user_id": "your_user_id"}
)
```
