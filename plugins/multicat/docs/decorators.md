# The `@option` Decorator

> Extend Cheshire Cat without changing its core code

The `@option` decorator is how Multicat adds features to Cheshire Cat without modifying its source code. This simple but powerful tool allows you to enhance existing classes with new functionality.

## How to Use It

```python
from cat.plugins.multicat.decorators import option

# Add new abilities to an existing class
@option(ExistingClass)
class BetterClass(ExistingClass):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Your extra initialization
    
    def new_feature(self):
        """Add brand new methods"""
        return "I can do new things now!"
```

## Examples from Multicat

### Adding Chat IDs to Messages

```python
@option(UserMessage)
class UserMessageWithChat(UserMessage):
    # Add new properties
    chat_id: str = "default"
    agent_id: str = "default"
```

### Adding Multi-Chat Support

```python
@option(StrayCat)
class FatherStrayCat(StrayCat, CommonStrayCat):
    """Enhances StrayCat with multi-chat capabilities"""
    
    def get_son(self, chat_id: str):
        """Get a specific chat context"""
        # Implementation that enables multi-chat functionality
        pass
```

## Tips for Success

1. **Always inherit** from the original class
2. **Test thoroughly** as your changes affect the whole system
3. **Keep it simple** - only modify what you need to change
4. **Document changes** so others understand your code

## When to Use It

Use the `@option` decorator when you need to:

- Add new properties to core classes
- Enhance existing methods with additional functionality
- Create feature extensions that need to integrate deeply with the core
