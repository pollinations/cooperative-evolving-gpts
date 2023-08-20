from typing import List, Optional, TypedDict
from pydantic import Field

class Message(TypedDict):
    to: str
    message: str

class ChatGPTMessage(TypedDict, total=False):
    role: str  # "system", "user", "function", "assistant"
    content: str
    name: Optional[str]  # only used in function calls

class Player(TypedDict):
    name: str
    dna: List[str]
    secret: str
    points: int
    history: List[ChatGPTMessage]
