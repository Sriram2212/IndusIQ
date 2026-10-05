from dataclasses import dataclass


@dataclass
class RetrievalResult:

    source: str

    content: any

    metadata: dict