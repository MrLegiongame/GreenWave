"""
Direction Module

This module contains the Direction class and related validation functions for managing
directions within junctions in the traffic simulation system. A Direction represents
a set of incoming and outgoing lanes associated with a road and a junction.

Classes:
    Direction: Represents a direction at a junction with associated lanes.

Functions:
    check_possible_collision: Checks for possible collisions between two lanes.
    check_direction_validity: Validates a list of lanes for direction creation.
"""

from classes.Nodes.Lane import Lane
from screens.functions import find_obj_index_in_array
from classes.Enums.LaneFacing import LaneFacing


def check_possible_collision(left_lane, right_lane):
    """
    Check for possible collisions between two lanes based on their to_lanes.
    
    Args:
        left_lane (Lane): The left lane to check
        right_lane (Lane): The right lane to check
        
    Raises:
        TypeError: If a possible collision is detected between the lanes
    """
    if not left_lane.to_lanes or not right_lane.to_lanes:
        return  # No collision possible if no lanes to connect
    if (left_lane.to_lanes[0]) < (right_lane.to_lanes[-1]):
        raise TypeError("Direction is invalid: Possible collision between different lanes")


def check_direction_validity(lanes):  # lanes: list[Lane]
    """
    Validate a list of lanes for direction creation.
    
    Args:
        lanes (list of Lane): The list of lanes to validate
        
    Returns:
        bool: True if all lanes are valid for direction creation
        
    Raises:
        TypeError: If the list or any lane is invalid, or if possible collisions are detected
    """
    if not isinstance(lanes, list):
        raise TypeError("Direction is invalid: Not a list")
    size = 0

    for lane in lanes:
        if not isinstance(lane, Lane):
            raise TypeError("Direction is invalid: Non-Lane value")
        if size >= 1:  # if at least the second lane (from the right)
            check_possible_collision(left_lane=lane, right_lane=lanes[size - 1])
        size += 1

    if not size >= 1:
        raise TypeError("Direction is invalid: No lanes")
    return True


class Direction:
    """
    Represents a direction at a junction with associated incoming and outgoing lanes.
    
    A Direction object manages the set of in-lanes and out-lanes for a particular
    direction at a junction, along with references to its parent junction and road.
    
    Attributes:
        in_lanes (list): List of incoming Lane objects (right to left)
        out_lanes (list): List of outgoing Lane objects (right to left)
        in_size (int): Number of incoming lanes
        out_size (int): Number of outgoing lanes
        size (int): Total number of lanes (in + out)
        parent_junction: Reference to the parent Junction object
        index_in_map (int): Index of this direction in the map
        module_index (int): Module index for state creation in Junction
        road: Reference to the associated Road object
    """

    def __init__(self, index_in_map, road=None, in_lanes=None, out_lanes=None):
        """
        Initialize a new Direction instance.
        
        Args:
            index_in_map (int): Index of this direction in the map
            road: Reference to the associated Road object (optional)
            in_lanes (list of Lane, optional): List of incoming lanes
            out_lanes (list of Lane, optional): List of outgoing lanes
        """
        self.in_lanes = []  # the logical order is from the right to the left
        self.out_lanes = []  # the logical order is from the right to the left
        self.in_size = 0
        self.out_size = 0
        self.size = 0
        self.parent_junction = None
        self.index_in_map = index_in_map
        self.module_index = None  # used for states creation in Junction
        self.road = road

        if None is not in_lanes:
            try:
                check_direction_validity(in_lanes)
                self.in_lanes = in_lanes
                self.in_size = len(in_lanes)
                self.size += self.in_size
                self.__set_lanes(in_lanes)
            except Exception:
                # Direction couldn't be created
                pass

        if None is not out_lanes:
            try:
                check_direction_validity(out_lanes)
                self.out_lanes = out_lanes
                self.out_size = len(out_lanes)
                self.size += self.out_size
                self.__set_lanes(out_lanes)
            except Exception:
                # Direction couldn't be created
                pass

    def __set_lanes(self, lanes):
        for lane in lanes:
            lane.set_parent_direction(self)

    def set_parent_junction(self, parent_junction):  # parent_junction: Junction
        """
        Set the parent junction for this direction.
        
        Args:
            parent_junction: The parent Junction object
        """
        self.parent_junction = parent_junction

    def set_road(self, road):
        """
        Set the associated road for this direction.
        
        Args:
            road: The Road object to associate with this direction
        Returns:
            bool: True if the road was set successfully, False otherwise
        """
        from classes.Edges.Road import Road
        if isinstance(road, Road):
            self.road = road
            return True
        return False

    def add_to_left(self, lane):  # lane: Lane
        """
        Add a lane to the left side of this direction (in-lane or out-lane).
        
        Args:
            lane (Lane): The lane to add
        Returns:
            bool: True if the lane was added successfully, False otherwise
        """
        if LaneFacing.IN == lane.facing:
            self.in_lanes.append(lane)
            self.in_size += 1
            return True
        elif LaneFacing.OUT == lane.facing:
            self.out_lanes.append(lane)
            self.out_size += 1
            return True
        return False

    def set_lane_as_direction_tuple(self, lane, index):  # lane: tuple[Direction], index: int
        """
        Set a lane as a tuple of directions at a specific index.
        
        Args:
            lane (tuple of Direction): The tuple of directions to set
            index (int): The index at which to set the tuple
        Raises:
            TypeError: If the direction or lane is not a tuple, or if index is out of range
        """
        if not isinstance(self.direction, tuple):
            raise TypeError(f"Setting lane {index} as tuple[Direction] is invalid: direction not a tuple")
        if self.size <= index or 0 > index:
            raise TypeError(f"Setting lane {index} as tuple[Direction] is invalid: index out of range")
        if not isinstance(lane, tuple):
            raise TypeError(f"Setting lane {index} as tuple[Direction] is invalid: given lane not a tuple")
        for direction in lane:
            if not isinstance(direction, Direction):
                raise TypeError(f"Setting lane {index} as tuple[Direction] is invalid: direction not a Direction")
        self.direction[index].lane = lane

    def __str__(self):
        res = f"Direction #{self.index_in_map}:\n\tIn Lanes:\n"
        for lane in self.in_lanes:
            if isinstance(lane, Lane):
                res += f"\t\t{lane}\n"
        res += "\n\tOut Lanes:\n"
        for lane in self.out_lanes:
            if isinstance(lane, Lane):
                res += f"\t\t{lane}\n"
        return res
