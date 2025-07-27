"""
Traffic Light States Module

This module contains the State enumeration for defining traffic light states
in the simulation system. These states represent the different phases of
traffic light operation and are used throughout the traffic control system.

Classes:
    State: Enumeration of traffic light states.

Constants:
    STATE_SIZE: Total number of available traffic light states.
"""

from enum import Enum


class State(Enum):
    """
    Enumeration of traffic light states.
    
    This enum defines the different states that traffic lights can be in
    during operation. These states follow standard traffic light behavior
    and are used by traffic control algorithms to manage signal timing.
    
    Values:
        RED: Red light - stop all traffic
        RED_YELLOW: Red and yellow lights - prepare to go (transition state)
        GREEN: Green light - proceed with caution
        GREEN_FLICKERING: Flashing green light - warning of upcoming change
        YELLOW: Yellow light - stop if safe to do so
    """
    RED = 0
    RED_YELLOW = 1
    GREEN = 2
    GREEN_FLICKERING = 3
    YELLOW = 4


# Total number of available traffic light states
STATE_SIZE = len(State)
