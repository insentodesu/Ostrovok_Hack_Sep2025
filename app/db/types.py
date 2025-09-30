import json
from typing import Any

from sqlalchemy.types import TypeDecorator, Text


class JSONEncodedList(TypeDecorator):
    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect) -> str | None:  
        if value is None:
            return None
        if not isinstance(value, list):
            raise TypeError("JSONEncodedList only accepts Python list values")
        return json.dumps(value, ensure_ascii=False)

    def process_result_value(self, value: Any, dialect) -> list[str]:
        if value is None:
            return []
        try:
            decoded = json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return []
        if isinstance(decoded, list):
            return decoded
        return []