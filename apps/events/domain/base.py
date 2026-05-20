from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any


@dataclass
class BaseEvent:
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def serialize(self):
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "payload": self.payload,
            "created_at": self.created_at.isoformat(),
        }
