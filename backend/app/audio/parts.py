from typing import Any


def audio_parts(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """The clips of an item. Single-clip items (listening, repeat) keep script/audio_key on the payload itself;
    an interview keeps one clip per question in payload['audio_parts']. Returned dicts alias the payload."""
    if "audio_parts" in payload:
        return payload["audio_parts"]
    if "script" in payload:
        return [payload]
    return []
