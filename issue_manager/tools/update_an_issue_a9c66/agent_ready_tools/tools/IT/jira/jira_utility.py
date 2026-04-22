from typing import Any


def adf_paragraph(text: str) -> dict[str, Any]:
    """Return a minimal Atlassian Document Format (ADF) paragraph document."""
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": text}],
            }
        ],
    }
