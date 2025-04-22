# Multicat Agents

> Multiple AI personalities in one Cheshire Cat

## What Are Agents?

Agents are specialized AI personalities with dedicated instructions and behaviors. Each agent can respond differently to the same question based on its defined role and expertise.

## Agent Structure

The `Agent` class is defined in `types.py`:

```python
class Agent(BaseModel):
    id: str = "default"
    name: str = ""
    instructions: str = ""
    metadata: Dict = Field(default_factory=dict)
```

## How to use

When send a message, include the `agent_id` field.

```json
{
    "text": "Explain what is the CheshireCat",
    "agent_id": "pieroit"
}
```

## Fields

| Property | Type | Description |
|----------|------|-------------|
| `id` | string | Unique identifier for the agent |
| `name` | string | Descriptive name for the agent |
| `instructions` | string | System instructions that define behavior |
| `metadata` | dict | Additional data for customization |

## How Agents Work

Agents change the AI's behavior through the `agent_prompt_prefix` hook. When a message is sent with a specific `agent_id`, the hook applies the agent's instructions:

```python
@hook(priority=0)
def agent_prompt_prefix(prefix, cat):
    if isinstance(cat, SonStrayCat):
        return cat.get_instructions() or prefix
    
    return prefix
```

This replaces the standard system prompt with the agent's custom instructions.