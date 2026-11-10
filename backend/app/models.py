from dataclasses import dataclass, field


@dataclass(frozen=True)
class Product:
    id: str
    title: str
    description: str
    handle: str = ""
    price: str = ""
    variants: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Policy:
    type: str
    body: str


@dataclass(frozen=True)
class Citation:
    id: str
    kind: str
    handle: str = ""


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    citations: list[Citation]
    deflected: bool = False
