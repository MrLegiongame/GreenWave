"""
Edge Density Module

This module contains the EdgeDensity enumeration for defining traffic density
levels on road edges in the simulation system. Density levels are used to
categorize traffic conditions and may influence algorithm behavior.

Classes:
    EdgeDensity: Enumeration of traffic density levels.

Constants:
    EDGE_DENSITY_SIZE: Total number of available density levels.
"""

from enum import Enum


class EdgeDensity(Enum):
    """
    Enumeration of traffic density levels on road edges.
    
    This enum defines different levels of traffic density that can be used
    to categorize traffic conditions on road segments. Density levels may
    influence traffic light timing algorithms and simulation parameters.
    
    Values:
        LOW: Low traffic density with minimal congestion
        MEDIUM: Medium traffic density with moderate congestion
        HIGH: High traffic density with significant congestion
    """
    LOW = 1
    MEDIUM = 2
    HIGH = 3


# Total number of available density levels
EDGE_DENSITY_SIZE = len(EdgeDensity)
