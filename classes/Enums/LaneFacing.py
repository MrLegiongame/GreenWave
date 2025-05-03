from enum import Enum


class LaneFacing(Enum):
    IN = 0
    OUT = 1


LANE_FACING_SIZE = len(LaneFacing)
