"""
Traffic Light Module

This module contains the TrafficLight class and related functions for managing
traffic lights within junctions in the simulation system. A TrafficLight controls
a group of lanes and manages their states based on traffic control algorithms.

Classes:
    TrafficLight: Represents a traffic light controlling multiple lanes.

Functions:
    check_traffic_light_validity: Validates a list of lanes for traffic light creation.
"""

from typing import Set

from classes.Nodes.Lane import Lane
from classes.Enums.State import State, STATE_SIZE
from screens.functions import are_there_possible_collisions, get_blocked_traffic_lights_by_traffic_lights, \
    get_blocked_traffic_lights_by_traffic_light


def check_traffic_light_validity(lanes):  # lanes: list[Lane]
    """
    Checks whether the values are valid (e.g. no future overflows nor possible collisions)
    each lane of a traffic light is sorted from right (index 0) to left (index len(lanes) - 1)
    
    Args:
        lanes (list of Lane): The list of lanes to validate for traffic light creation
        
    Returns:
        bool: True if all lanes are valid for traffic light creation
        
    Raises:
        TypeError: If the list is invalid, empty, contains non-Lane objects, or has collisions
    """
    if not isinstance(lanes, list):
        raise TypeError("Traffic Light is invalid: Not a list parameter was given")
    size = 0
    for lane in lanes:
        if not isinstance(lane, Lane):
            raise TypeError("Traffic Light is invalid: Non-Lane value")
        size += 1
    if not (size >= 1):
        raise TypeError("Traffic Light is invalid: Not enough lanes")
    if are_there_possible_collisions(lanes):
        raise TypeError("Traffic Light is invalid: Possible collisions detected")
    return True


class TrafficLight:
    """
    Represents a traffic light that controls multiple lanes within a junction.
    
    A TrafficLight manages a group of lanes that can be controlled together
    without causing conflicts. It maintains the current state and provides
    methods for state transitions and conflict detection.
    
    Attributes:
        key (str): Unique identifier for this traffic light
        lanes (list): List of Lane objects controlled by this traffic light
        size (int): Number of lanes controlled by this traffic light
        current_state (State): Current state of the traffic light
    """

    def __init__(self, key, lanes=None):
        """
        Initialize a new TrafficLight instance.
        
        Args:
            key (str): Unique identifier for this traffic light
            lanes (list of Lane, optional): List of lanes to control
        """
        self.key = key
        self.lanes = None
        self.size = None
        self.current_state = None
        self.set_lanes(lanes)

    def set_lanes(self, lanes):
        """
        Set the lanes controlled by this traffic light.
        
        Args:
            lanes (list of Lane): List of lanes to control
            
        Returns:
            bool: True if lanes were set successfully, False otherwise
        """
        if None is lanes:
            return False
        try:
            check_traffic_light_validity(lanes)
            self.lanes = lanes
            self.size = len(lanes)
        except Exception as e:
            print(f"Traffic Light couldn't be created due to this error: {e}")
            return False
        return True

    def set_state(self, state):
        """
        Set the current state of the traffic light and update all controlled lanes.
        
        Args:
            state (State): The new state to set
            
        Returns:
            bool: True if state was set successfully, False otherwise
        """
        if not isinstance(state, State):
            return False
        self.current_state = state
        for lane in self.lanes:
            lane.set_cur_state(self.current_state)
        return True

    def update_state(self):
        """
        Update the traffic light state to the next state in the cycle.
        
        This method cycles through the available states (RED, RED_YELLOW, GREEN,
        GREEN_FLICKERING, YELLOW) and updates all controlled lanes accordingly.
        """
        self.current_state = State((self.current_state.value + 1) % STATE_SIZE)
        for lane in self.lanes:
            lane.update_state()

    def get_direction(self):
        """
        Get the parent direction of the first lane in this traffic light.
        
        Returns:
            Direction or None: The parent direction, or None if no lanes exist
        """
        if None is self.lanes:
            return None
        return self.lanes[0].parent_direction

    def get_directions_directing_indexes(self):
        """
        Get the module indexes of all directions that this traffic light directs to.
        
        Returns:
            list: List of direction module indexes that this traffic light directs to
        """
        directions_directing_indexes = set()
        for lane in self.lanes:
            for to_lane in lane.to_lanes:
                directions_directing_indexes.add(to_lane.parent_direction.module_index)
        return list(directions_directing_indexes)

    def get_minimum_to_lane_index_by_direction(self, direction):
        """
        Get the minimum lane index for a specific direction that this traffic light directs to.
        
        Args:
            direction (Direction): The direction to find the minimum lane index for
            
        Returns:
            int or float: The minimum lane index, or infinity if no lanes found
        """
        indexes = []
        for lane in self.lanes:
            for to_lane in lane.to_lanes:
                if to_lane.parent_direction is direction:
                    indexes.append(to_lane.index_in_junction)
        if indexes:
            return min(indexes)
        return float('inf')

    def get_maximum_to_lane_index_by_direction(self, direction):
        """
        Get the maximum lane index for a specific direction that this traffic light directs to.
        
        Args:
            direction (Direction): The direction to find the maximum lane index for
            
        Returns:
            int: The maximum lane index, or -1 if no lanes found
        """
        indexes = []
        for lane in self.lanes:
            for to_lane in lane.to_lanes:
                if to_lane.parent_direction is direction:
                    indexes.append(to_lane.index_in_junction)
        if indexes:
            return max(indexes)
        return -1

    def get_weight(self, included: Set['TrafficLight'], junction) -> int:
        """
        Calculate the weight of this traffic light for optimization algorithms.
        
        The weight represents the number of lanes that would be blocked if this
        traffic light is activated, excluding those already blocked by included
        traffic lights.
        
        Args:
            included (Set[TrafficLight]): Set of traffic lights already included
            junction (Junction): The parent junction
            
        Returns:
            int: The weight value for this traffic light
        """
        blocked_traffic_lights_by_self = get_blocked_traffic_lights_by_traffic_light(junction, self)
        blocked_traffic_lights_by_included = get_blocked_traffic_lights_by_traffic_lights(junction, included)

        blocked_traffic_lights_for_weight = blocked_traffic_lights_by_self - blocked_traffic_lights_by_included
        weight = 0
        for traffic_light in blocked_traffic_lights_for_weight:
            weight += traffic_light.size
        return weight

    def __repr__(self):
        """
        Get string representation of this traffic light.
        
        Returns:
            str: The key identifier of this traffic light
        """
        return self.key

    def __eq__(self, other):
        """
        Check if this traffic light equals another traffic light.
        
        Args:
            other: The other traffic light to compare with
            
        Returns:
            bool: True if both traffic lights have the same key
        """
        return isinstance(other, TrafficLight) and self.key == other.key

    def __hash__(self):
        """
        Get hash value for this traffic light.
        
        Returns:
            int: Hash value based on the traffic light key
        """
        return hash(self.key)
