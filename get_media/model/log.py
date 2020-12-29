from dataclasses import dataclass


@dataclass
class Log:
    type: str
    time: int
    user: dict
    data: dict
