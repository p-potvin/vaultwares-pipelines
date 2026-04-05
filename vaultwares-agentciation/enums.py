from enum import Enum

class AgentStatus(Enum):
    LOST = 'LOST'
    WORKING = 'WORKING'
    WAITING_FOR_INPUT = 'WAITING_FOR_INPUT'
    RELAXING = 'RELAXING'
