"""
Lane Facing Module

This module contains the LaneFacing enumeration for defining the direction
that lanes face within junctions in the traffic simulation system. Lane
facing is crucial for determining traffic flow direction and pathfinding.

Classes:
    LaneFacing: Enumeration of lane direction types.

Constants:
    LANE_FACING_SIZE: Total number of available facing directions.
"""

from enum import Enum


class LaneFacing(Enum):
    """
    Enumeration of lane direction types within junctions.
    
    This enum defines the two possible directions that lanes can face
    within a junction. This information is essential for determining
    traffic flow direction and for pathfinding algorithms.
    
    Values:
        IN: Lane facing into the junction (incoming traffic)
        OUT: Lane facing out of the junction (outgoing traffic)
    """
    IN = 0
    OUT = 1


# Total number of available facing directions
LANE_FACING_SIZE = len(LaneFacing)
