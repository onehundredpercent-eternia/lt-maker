
from ast import Dict
from app.events.event_prefab import EventCatalog
from app.events.python_eventing.analyzer import EventContext
from app.utilities.typing import NID

class EventAnalyzer():
    def __init__(self, event_db: EventCatalog = None) -> None:
        self._catalog: EventCatalog = event_db

    def verify_conditional_blocks(self):
        pass