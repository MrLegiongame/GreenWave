from enum import Enum


class State(Enum):
    RED = 0
    RED_YELLOW = 1
    GREEN = 2
    GREEN_FLICKERING = 3
    YELLOW = 4


STATE_SIZE = len(State)
