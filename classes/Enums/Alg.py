"""
Algorithm Types Module

This module contains the Alg enumeration for defining different types of traffic
control algorithms used in the simulation system. Each algorithm type represents
a different strategy for managing traffic light timing and coordination.

Classes:
    Alg: Enumeration of traffic control algorithm types.

Constants:
    ALGORITHM_SIZE: Total number of available algorithm types.
"""

from enum import Enum


class Alg(Enum):
    """
    Enumeration of traffic control algorithm types.
    
    This enum defines the different algorithms available for controlling
    traffic lights in the simulation system. Each algorithm implements
    a different strategy for optimizing traffic flow.
    
    Values:
        FIXED_TIMING_CYCLE: Fixed timing cycle algorithm with predetermined intervals
        ADAPTIVE_ALG: Adaptive algorithm that responds to current traffic conditions
        GREEN_WAVE_ENERGY: Green wave algorithm optimized for energy consumption
        GREEN_WAVE_POLLUTION: Green wave algorithm optimized for pollution reduction
    """
    FIXED_TIMING_CYCLE = 0
    ADAPTIVE_ALG = 1
    GREEN_WAVE_ENERGY = 2
    GREEN_WAVE_POLLUTION = 3


# Total number of available algorithm types
ALGORITHM_SIZE = len(Alg)
