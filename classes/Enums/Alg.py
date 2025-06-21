from enum import Enum


class Alg(Enum):
    FIXED_TIMING_CYCLE = 0
    ADAPTIVE_ALG = 1
    GREEN_WAVE = 2


ALGORITHM_SIZE = len(Alg)
