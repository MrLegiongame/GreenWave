from enum import Enum


class Alg(Enum):
    FIXED_TIMING_CYCLE = 0
    GREEN_WAVE = 1


ALGORITHM_SIZE = len(Alg)
