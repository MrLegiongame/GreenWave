from enum import Enum


class Alg(Enum):
    FIXED_TIMING_CYCLE = 0
    ADAPTIVE_ALG = 1
    GREEN_WAVE_ENERGY = 2
    GREEN_WAVE_POLLUTION = 3


ALGORITHM_SIZE = len(Alg)
