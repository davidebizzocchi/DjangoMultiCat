# Multicat Caching System

> Efficient memory management for multi-chat environments

Multicat implements a sophisticated caching system to manage multiple chat contexts while maintaining performance and memory efficiency.

## Cache Hierarchy

```markdown
┌─────────────────────────────────────────────────┐
│                 UserFatherCache                 │
│     (System-wide cache of all user contexts)    │
│                                                 │
│  ┌─────────────────────────────────────────┐    │
│  │           FatherSonCache (user1)        │    │
│  │     (All chats for a specific user)     │    │
│  │                                         │    │
│  │   ┌─────────┐   ┌─────────┐   ┌─────┐   │    │
│  │   │ Chat 1  │   │ Chat 2  │   │ ... │   │    │
│  │   └─────────┘   └─────────┘   └─────┘   │    │
│  └─────────────────────────────────────────┘    │
│                                                 │
│  ┌─────────────────────────────────────────┐    │
│  │           FatherSonCache (user2)        │    │
│  │                  ...                    │    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

## Cache Components

### BaseStrayCache

The foundation class that extends Cheshire Cat's `InMemoryCache` with:

| Feature | Description |
|---------|-------------|
| Auto-cleanup | Intelligently removes old entries when the cache gets full |
| Protected keys | Prevents essential items from being removed |
| Configurable limits | Customizable cache size and cleanup behavior |

### Specialized Caches

#### UserFatherCache

```python
class UserFatherCache(BaseStrayCache):
    def __init__(self, max_items=100, precision=0.2, protected_keys=["user"]):
        # Configuration for user-level cache
        super().__init__(
            max_items=max_items,
            precision=precision,
            protected_keys=protected_keys
        )
```

- **Purpose**: Stores all user contexts (FatherStrayCats)
- **Default Size**: 100 users
- **Cleanup Strategy**: Removes 20% of oldest entries when full
- **Protected**: The "user" key is never removed

#### FatherSonCache

```python
class FatherSonCache(BaseStrayCache):
    def __init__(self, max_items=4, precision=1, protected_keys=["default"]):
        # Configuration for chat-level cache
        super().__init__(
            max_items=max_items,
            precision=precision,
            protected_keys=protected_keys
        )
```

- **Purpose**: Stores all chat contexts for a specific user
- **Default Size**: 4 active chats per user
- **Cleanup Strategy**: Removes all old entries when full
- **Protected**: The "default" chat is never removed

## Configuring Cache Parameters

You can customize the cache behavior through the plugin settings in the Cheshire Cat admin interface:

| Setting Name | Description | Default Value |
|--------------|-------------|---------------|
| `max_users` | Maximum number of users in cache | 100 |
| `users_timeout` | How long user data is kept (seconds) | 3600 |
| `max_chat_sessions` | Maximum chats per user | 100 |
| `chat_session_timeout` | How long chat data is kept (seconds) | 3600 |

### Through Admin UI

1. Go to the Cheshire Cat admin interface
2. Navigate to Plugins → Multicat → Settings
3. Adjust the cache parameters as needed
4. Save your changes

### In Custom Plugins

If you're developing extensions to Multicat, you can access these settings in your code:

```python
from cat.plugins.multicat.settings import MultiCatSettings

def my_plugin_function(cat):
    # Get the current settings
    settings = cat.settings
    
    # Use the settings
    max_chats = settings.max_chat_sessions
    timeout = settings.chat_session_timeout
    
    # Your logic here...
```

## Cache Operations

### Automatic Cleanup Logic

When a cache becomes full, Multicat:

1. Calculates how many items to remove based on the precision setting
2. Preserves protected items regardless of age
3. Removes the oldest non-protected items

## Performance Tuning

For different deployment scenarios, consider adjusting:

| Parameter | Default | Recommended Change |
|-----------|---------|-------------------|
| UserFatherCache max_items | 100 | Increase for systems with many users |
| FatherSonCache max_items | 4 | Increase for users with many chats |
| TTL values | 3600s (1h) | Adjust based on session patterns |

This caching architecture ensures Multicat can efficiently handle multiple concurrent chat contexts without memory issues, even in busy environments.
