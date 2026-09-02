from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any


class InvalidCanonicalJsonError(ValueError):
    pass


@dataclass(frozen=True)
class CanonicalJson:
    value: dict[str, Any]
    encoded: bytes
    sha256: str


def canonical_json(value: dict[str, Any]) -> CanonicalJson:
    _validate_json(value, path="$")
    text = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    encoded = text.encode("utf-8")
    normalized = json.loads(text)
    return CanonicalJson(
        value=normalized,
        encoded=encoded,
        sha256=hashlib.sha256(encoded).hexdigest(),
    )


def _validate_json(value: Any, path: str) -> None:
    if value is None or isinstance(value, (bool, str, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise InvalidCanonicalJsonError(f"{path} contains a non-finite number")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise InvalidCanonicalJsonError(
                    f"{path} contains a non-string object key"
                )
            _validate_json(item, f"{path}.{key}")
        return
    raise InvalidCanonicalJsonError(
        f"{path} contains unsupported JSON value {type(value).__name__}"
    )
