from dataclasses import dataclass


@dataclass
class ChatContext:
    user_id: str
    session_id: str
