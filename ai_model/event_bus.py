"""
Simple in-process event/message bus for multi-agent coordination.
"""
from typing import Callable, Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class EventBus:
    _subscribers: Dict[str, List[Callable[[Any], None]]] = {}

    @classmethod
    def subscribe(cls, event_type: str, handler: Callable[[Any], None]):
        if event_type not in cls._subscribers:
            cls._subscribers[event_type] = []
        cls._subscribers[event_type].append(handler)
        logger.info(f"Subscribed handler to event '{event_type}'")

    @classmethod
    def publish(cls, event_type: str, data: Any):
        handlers = cls._subscribers.get(event_type, [])
        logger.info(f"Publishing event '{event_type}' to {len(handlers)} handlers")
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                logger.error(f"Error in event handler for '{event_type}': {e}")

    @classmethod
    def clear(cls):
        cls._subscribers.clear()

# Example usage:
# EventBus.subscribe('error', lambda data: print('Error:', data))
# EventBus.publish('error', {'msg': 'Something went wrong'})
