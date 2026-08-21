from collections.abc import Iterator
from typing import Protocol, TypedDict


class StreamPart(TypedDict):
    kind: str  # "thinking" | "answer"
    text: str


class ChatGenerator(Protocol):
    def generate(
        self, question: str, context: str, history: list[tuple[str, str]]
    ) -> str: ...

    def generate_stream(
        self, question: str, context: str, history: list[tuple[str, str]]
    ) -> Iterator[StreamPart]: ...
