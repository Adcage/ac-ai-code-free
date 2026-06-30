import asyncio
from dataclasses import dataclass

from app.runtime.events import RuntimeEvent


@dataclass(frozen=True)
class SequencedRuntimeEvent:
    agent_run_id: int
    seq: int
    event: RuntimeEvent


class EventBus:
    def __init__(self, agent_run_id: int):
        self.agent_run_id = agent_run_id
        self._seq = 0
        self._queue: asyncio.Queue[SequencedRuntimeEvent | None] = asyncio.Queue()
        self._history: list[SequencedRuntimeEvent] = []

    async def emit(self, event: RuntimeEvent) -> None:
        self._seq += 1
        sequenced = SequencedRuntimeEvent(
            agent_run_id=self.agent_run_id,
            seq=self._seq,
            event=event,
        )
        self._history.append(sequenced)
        await self._queue.put(sequenced)

    async def next_event(self) -> SequencedRuntimeEvent | None:
        return await self._queue.get()

    def snapshot(self) -> list[SequencedRuntimeEvent]:
        return list(self._history)

    async def close(self) -> None:
        await self._queue.put(None)
