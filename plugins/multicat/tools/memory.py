import json
from cat.mad_hatter.decorators import tool

from cat.plugins.multicat.refactory.stray_cat.son import SonStrayCat
from cat.log import log


@tool(
    return_direct=True,
    examples=[
        "What file you know?"
    ]
)
def get_file_list(tool_input, cat):
    """What file you know? Input is None."""

    files = cat.get_file_list()

    formatted_output = json.dumps(files, indent=2)
    return f"""
You have this files:
```json
{formatted_output}
```
"""
