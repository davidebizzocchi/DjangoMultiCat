# Multicat

[![awesome plugin](https://custom-icon-badges.demolab.com/static/v1?label=&message=awesome+plugin&color=F4F4F5&style=for-the-badge&logo=cheshire_cat_black)](https://)

## Multicat Plugin for Cheshire Cat

### Bost Your Cheshire Cat with Native Multichat Support

[![Plugin Version](https://img.shields.io/badge/version-0.0.1-blue)](https://github.com/davidebizzocchi/multicat)

The Multicat plugin extends the Cheshire Cat AI framework with native multichat capabilities, enabling simultaneous independent conversations and file management per chat session - all without needing to fork the core project.

## Key Features

🚀 **Native Multichat Support**  
Maintain separate conversation histories and working memories for each chat session

📁 **Chat-Specific File Management**  
Automatically handle different files and metadata for individual conversations

🧠 **Enhanced Memory Management**  
Custom endpoints for granular control over vector memories and conversation history

🔌 **Zero-Friction Installation**  
Works with official Cheshire Cat Docker images - no custom builds required

🔮 **Multi-Agent Foundation**  
Lays groundwork for future multi-agent capabilities (in development)

## Quick Start

### Installation

1. Install the MultiCat plugin for registry (inside your admin)

2. Activate the plugin

3. Restart your Cheshire Cat instance

Now, MultiCat will be loaded with the CheshireCat and do its magic.

## Core Functionality

### Cheshire Classes  

This system uses two main classes:  

- **FatherStrayCat**: Extends the `StrayCat` class and manages multiple chat instances (its "sons").  
- **SonStrayCat**: Also extends `StrayCat` (a copy) and manages an individual chat, identified by `chat_id`.  

## Decorators  

The **@option** decorator allows overriding a common class by instantiating another class before it (overriding the `__new__` method).  

Here’s the relevant code:  

```python
@option(StrayCat)
class FatherStrayCat(StrayCat):
```

### Endpoints

| Endpoint                          | Method | Description                                  |
|-----------------------------------|--------|----------------------------------------------|
| `/memory/working_memories`        | GET    | List all active chat sessions                |
| `/memory/working_memories/{chat_id}` | GET | Retrieve specific chat history               |
| `/memory/conversation_history`    | DELETE | Clear current chat history                   |
| `/memory/collections/{collection_id}/points/metadata` | PATCH | Bulk update memory metadata |

## Django Integration

For a ready-to-use chat interface with multichat support, use our companion Django project:  
[DjangoMultiCat Repository](https://github.com/davidebizzocchi/DjangoMultiCat)

Key features of the Django interface:

- User-friendly chat management
- Visual file organization per conversation
- Easy integration with existing Cheshire Cat instances

## Roadmap

- [x] Multi-agent conversation support
- [x] Web interface integration
- [ ] Manage Tool
- [ ] Tool creation endpoint
