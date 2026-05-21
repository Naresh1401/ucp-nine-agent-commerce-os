from threading import Lock
from typing import Optional

from ucp_nine.models import AgentTrace, UcpJourneyResult


class JourneyStore:
    def __init__(self) -> None:
        self._journeys: dict[str, UcpJourneyResult] = {}
        self._idempotency: dict[str, str] = {}
        self._events: dict[str, list[AgentTrace]] = {}
        self._lock = Lock()

    def get_by_idempotency_key(self, key: str) -> Optional[UcpJourneyResult]:
        with self._lock:
            journey_id = self._idempotency.get(key)
            if not journey_id:
                return None
            return self._journeys[journey_id]

    def save(self, key: str, result: UcpJourneyResult) -> None:
        with self._lock:
            self._journeys[result.journey_id] = result
            self._idempotency[key] = result.journey_id
            self._events[result.journey_id] = result.trace

    def get(self, journey_id: str) -> Optional[UcpJourneyResult]:
        with self._lock:
            return self._journeys.get(journey_id)

    def events(self, journey_id: str) -> list[AgentTrace]:
        with self._lock:
            return self._events.get(journey_id, [])
