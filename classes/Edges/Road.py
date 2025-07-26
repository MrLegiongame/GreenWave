"""
Road Module

This module contains the Road class and related validation functions for managing
road infrastructure in the traffic simulation system. A Road represents a connection
between two junctions with multiple lanes in both directions.

Classes:
    Road: Represents a road segment connecting two junctions with bidirectional traffic.

Functions:
    check_road_validity: Validates road parameters before road creation.
"""

from classes.Edges.RoadLane import RoadLane
from classes.Nodes.Direction import Direction
import math


def check_road_validity(name, first_direction, second_direction, length):
    """
    Validates road parameters to ensure they meet the requirements for road creation.
    
    Args:
        name (str): The name identifier for the road
        first_direction (Direction): The first direction object representing one end of the road
        second_direction (Direction): The second direction object representing the other end of the road
        length (int): The length of the road in meters (must be positive)
    
    Returns:
        bool: True if all parameters are valid
        
    Raises:
        TypeError: If any parameter is of incorrect type or has invalid values
    """
    if not isinstance(name, str):
        raise TypeError("Road is invalid: Non-string value was given")
    if not isinstance(first_direction, Direction):
        raise TypeError("Road is invalid: Non-Direction value was given")
    if not isinstance(second_direction, Direction):
        raise TypeError("Road is invalid: Non-Direction value was given")
    if not isinstance(length, int):
        raise TypeError("Road is invalid: Non-int value was given")
    if not (length > 0):
        raise TypeError("Road is invalid: length with non-positive value")
    if not (first_direction.out_size == second_direction.in_size):
        raise TypeError("Road is invalid: Not equal number of lanes")
    if not (first_direction.in_size == second_direction.out_size):
        raise TypeError("Road is invalid: Not equal number of lanes")
    return True


class Road:
    """
    Represents a road segment that connects two junctions with bidirectional traffic.
    
    A Road contains multiple lanes in both directions, each represented by RoadLane objects.
    The road maintains references to its connecting junctions through Direction objects
    and manages the flow of vehicles between them.
    
    Attributes:
        name (str): The unique identifier for this road
        first_direction (Direction): The direction object for the first junction
        second_direction (Direction): The direction object for the second junction
        length (float): The length of the road in kilometers
        maximum_speed (int): The maximum allowed speed on this road
        road_lanes_first_direction (list): List of RoadLane objects for first direction
        road_lanes_second_direction (list): List of RoadLane objects for second direction
        lanes_first_direction_size (int): Number of lanes in first direction
        lanes_second_direction_size (int): Number of lanes in second direction
    """

    def __init__(self, name, first_direction, second_direction, length, maximum_speed):
        """
        Initialize a new Road instance.
        
        Args:
            name (str): The name identifier for the road
            first_direction (Direction): The direction object for the first junction
            second_direction (Direction): The direction object for the second junction
            length (int): The length of the road in meters
            maximum_speed (int): The maximum allowed speed on this road
            
        Note:
            The length is automatically converted from meters to kilometers for internal storage.
            RoadLane objects are automatically created for each lane in both directions.
        """
        self.name = None
        self.first_direction = None
        self.second_direction = None
        self.length = None
        self.maximum_speed = None
        self.road_lanes_first_direction = []
        self.road_lanes_second_direction = []
        self.lanes_first_direction_size = 0
        self.lanes_second_direction_size = 0

        try:
            check_road_validity(name, first_direction, second_direction, length)

            self.name = name
            self.first_direction = first_direction
            self.second_direction = second_direction
            self.length = length / 1_000.0  # in Km
            self.maximum_speed = maximum_speed
            self.road_lanes_first_direction = []
            self.road_lanes_second_direction = []
            self.lanes_first_direction_size = first_direction.in_size
            self.lanes_second_direction_size = second_direction.in_size

            for lane in range(self.lanes_first_direction_size):
                self.road_lanes_first_direction.append(RoadLane(self, source_lane=second_direction.out_lanes[lane], destination_lane=first_direction.in_lanes[lane], length=length))
            for lane in range(self.lanes_second_direction_size):
                self.road_lanes_second_direction.append(RoadLane(self, source_lane=first_direction.out_lanes[lane], destination_lane=second_direction.in_lanes[lane], length=length))

        except Exception as e:
            print(f"RoadLane couldn't be created due to this error: {e}")

    def get_first_point(self):
        """
        Get the geographical coordinates of the first junction point.
        
        Returns:
            tuple or None: The (x, y) coordinates of the first junction point,
                          or None if the point is not available
        """
        if None is not self.first_direction:
            if None is not self.first_direction.parent_junction:
                if None is not self.first_direction.parent_junction.point:
                    return self.first_direction.parent_junction.point.get_point()

    def get_second_point(self):
        """
        Get the geographical coordinates of the second junction point.
        
        Returns:
            tuple or None: The (x, y) coordinates of the second junction point,
                          or None if the point is not available
        """
        if None is not self.second_direction:
            if None is not self.second_direction.parent_junction:
                if None is not self.second_direction.parent_junction.point:
                    return self.second_direction.parent_junction.point.get_point()
