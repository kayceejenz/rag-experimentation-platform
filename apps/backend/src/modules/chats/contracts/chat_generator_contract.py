from collections.abc import Iterator
from typing import Protocol


class ChatGenerator(Protocol):
    def generate(
        self, question: str, context: str, history: list[tuple[str, str]]
    ) -> str: ...

    def generate_stream(
        self, question: str, context: str, history: list[tuple[str, str]]
    ) -> Iterator[str]: ...
