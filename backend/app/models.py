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
