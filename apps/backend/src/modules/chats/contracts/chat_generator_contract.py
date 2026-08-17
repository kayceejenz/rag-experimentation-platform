from typing import Protocol


class ChatGenerator(Protocol):
    def generate(
        self, question: str, context: str, history: list[tuple[str, str]]
    ) -> str: ...
