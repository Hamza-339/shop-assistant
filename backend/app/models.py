from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    id: str
    title: str
    description: str


@dataclass(frozen=True)
class Policy:
    type: str
    body: str


@dataclass(frozen=True)
class Citation:
    id: str
    kind: str


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    citations: list[Citation]
