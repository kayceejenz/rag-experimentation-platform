from collections.abc import AsyncIterator
from typing import Protocol, TypedDict


class StreamPart(TypedDict):
    kind: str  # "thinking" | "answer"
    text: str


class ChatGenerator(Protocol):
    async def generate(
        self, question: str, context: str, history: list[tuple[str, str]]
    ) -> str: ...

    def generate_stream(
        self, question: str, context: str, history: list[tuple[str, str]]
    ) -> AsyncIterator[StreamPart]: ...
