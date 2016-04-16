from enum import Enum


class ThreadStatus(Enum):
    terminated = -1
    new = 0
    running = 1
    waiting = 2
    blocked = 3
