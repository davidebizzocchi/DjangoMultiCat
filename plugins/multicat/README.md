# Multicat

[![awesome plugin](https://custom-icon-badges.demolab.com/static/v1?label=&message=awesome+plugin&color=F4F4F5&style=for-the-badge&logo=cheshire_cat_black)](https://)

<img src="./logo.png" alt="MultiCat" width="400" height="400">

## Multicat Plugin for Cheshire Cat

Transform Cheshire Cat into a complete multi-cat framework.

Multicat extends the Cheshire Cat AI framework with native multichat and multiagent capabilities, enabling simultaneous independent conversations, file management per chat session, and the creation of custom agents.

By default declarative memory and episodic are separated for users.

**All without needing to modify the core project.**

For all your recipes [👨‍🍳 Cook Book](docs/readme.md)

### Key Features

- 💬 **Multi-chat**: Manage multiple conversations simultaneously, keeping them completely separate
- 🤖 **Multi-agent**: Create and customize different agents with specific personalities (currently only via prompts)
- 🗄️ **Conversation caching**: Automatic saving of conversations to continue at any time
- 🐝 **Complete API**: Dedicated endpoints for integration with other applications
- 🗂️ **File management per chat**: Associate and organize specific documents for each conversation

### Enhance Your Cheshire Cat with Native Multichat Support

## Quick Start

### Installation

1. Install the MultiCat plugin from the registry (within the admin panel)
2. Activate the plugin from settings
3. **Restart your Cheshire Cat instance**

Now MultiCat will be loaded with Cheshire Cat and automatically start working.

## Django Integration

For a ready-to-use chat interface with multichat support, use my companion Django project:  
[DjangoMultiCat Repository](https://github.com/davidebizzocchi/DjangoMultiCat)

Key features

- Intuitive chat management
- Visual organization of files for each conversation
- Easy integration with existing Cheshire Cat instances
- Responsive and customizable user interface

### Usage

Read the [👨‍🍳 Cook Book](docs/README.md).

#### Basic Usage

For send a message with a specific **chat_id**

- When sending a the message, specify a `chat_id`. The plugin will automatically create a new SonStrayCat and start a new chat.
- The response will include the associated `chat_id`.

**Example**

```json
{
    "text": "Hello",
    "chat_id": "first"
}
```

#### Working with Files and Metadata

##### Uploading Files with Metadata

Upload a file to the RabbitHole with specific metadata:

```python
# Python example
metadata = {
    "file_id": "unique_file_id",  # Unique identifier for your file
    "chats_id": ["chat1", "chat2"],  # Associate with specific chats
    "custom_field": "custom value"  # Any custom metadata
}

# Using requests
import requests
files = {"file": open("document.pdf", "rb")}
payload = {"metadata": json.dumps(metadata)}
response = requests.post(
    "http://localhost:1865/rabbithole/",
    files=files,
    data=payload,
    headers={"user_id": "your_user_id"}
)
```

##### Associating Files with Chats

Associate existing files with chats:

```python
# Add file to chats
response = requests.patch(
    "http://localhost:1865/memory/collections/declarative/points/edit_chat_ids?mode=add",
    json={
        "search_metadata": {"file_id": "unique_file_id"},
        "chats_id": ["chat1", "chat4"]
    },
    headers={"user_id": "your_user_id"}
)

# Remove file from chats
response = requests.patch(
    "http://localhost:1865/memory/collections/declarative/points/edit_chat_ids?mode=remove",
    json={
        "search_metadata": {"file_id": "unique_file_id"},
        "chats_id": ["chat1"]
    },
    headers={"user_id": "your_user_id"}
)
```

#### Agents

For agent you must specify the `agent_id` when send a message

**Example**

```json
{
    "text": "Hellooo",
    "chat_id": "first",
    "agent_id": "welcome"
}
```

## Roadmap

- [x] Multi-chat agent
- [x] File-chat association: RabbitHole + endpoints
- [x] Multi-agent: prompt hook + endpoints + stored
- [x] Web interface integration
- [x] Re-build conversation: endpoint
- [x] Cache: SonStrayCat
- [ ] Capabilities for agents: plugins, vector search, ...
- [ ] Custom tool creation

## Contributions

Contributions and feedback are welcome! Open an issue or a pull request on the repository.
