"""
RoadLane Module

This module contains the RoadLane class and related validation functions for managing
individual lanes within roads in the traffic simulation system. A RoadLane represents
a single lane that vehicles can travel on between two junctions.

Classes:
    RoadLane: Represents a single lane within a road that manages vehicle traffic.

Functions:
    check_road_lane_validity: Validates road lane parameters before lane creation.
"""

from classes.Entities.Vehicles.Vehicle import Vehicle


def check_road_lane_validity(parent_road, source_lane, destination_lane, length):
    """
    Validates road lane parameters to ensure they meet the requirements for lane creation.
    
    Args:
        parent_road (Road): The parent road object that contains this lane
        source_lane (Lane): The source lane object at one end of the road lane
        destination_lane (Lane): The destination lane object at the other end of the road lane
        length (int): The length of the road lane in meters (must be positive)
    
    Returns:
        bool: True if all parameters are valid
        
    Raises:
        TypeError: If any parameter is of incorrect type or has invalid values
    """
    from classes.Nodes.Lane import Lane
    from classes.Edges.Road import Road
    if not isinstance(parent_road, Road):
        raise TypeError("RoadLane is invalid: Non-Road value was given")
    if not isinstance(source_lane, Lane):
        raise TypeError("RoadLane is invalid: Non-Direction value was given")
    if not isinstance(destination_lane, Lane):
        raise TypeError("RoadLane is invalid: Non-Direction value was given")
    if not isinstance(length, int):
        raise TypeError("RoadLane is invalid: Non-int value was given")
    if not (length > 0):
        raise TypeError("RoadLane is invalid: length with non-positive value")
    return True


class RoadLane:
    """
    Represents a single lane within a road that manages vehicle traffic.
    
    A RoadLane connects a source lane from one junction to a destination lane at another
    junction. It maintains a list of vehicles currently traveling on this lane and provides
    methods for vehicle entry, exit, and traffic analysis.
    
    Attributes:
        parent_road (Road): The parent road object that contains this lane
        source_lane (Lane): The source lane object at one end of the road lane
        destination_lane (Lane): The destination lane object at the other end of the road lane
        length (int): The length of the road lane in meters
        vehicles (list): List of Vehicle objects currently on this lane
        vehicles_size (int): Number of vehicles currently on this lane
    """
    
    def __init__(self, parent_road, source_lane, destination_lane, length):
        """
        Initialize a new RoadLane instance.
        
        Args:
            parent_road (Road): The parent road object that contains this lane
            source_lane (Lane): The source lane object at one end of the road lane
            destination_lane (Lane): The destination lane object at the other end of the road lane
            length (int): The length of the road lane in meters
            
        Note:
            The source and destination lanes are automatically linked to this road lane
            by setting their road_lane attribute to this instance.
        """
        self.parent_road = None
        self.source_lane = None
        self.destination_lane = None
        self.length = None
        self.vehicles = []
        self.vehicles_size = 0

        try:
            check_road_lane_validity(parent_road, source_lane, destination_lane, length)
            self.parent_road = parent_road
            self.source_lane = source_lane
            self.source_lane.road_lane = self
            self.destination_lane = destination_lane
            self.destination_lane.road_lane = self
            self.length = length
        except Exception:
            # RoadLane couldn't be created
            return

    def get_list_of_vehicles_which_are_left_with_more_than_one_junction_sorted_by_arrival_time_from_and_to_seconds(self, from_seconds, to_seconds):
        """
        Get a list of vehicles that have more than one junction remaining in their route,
        sorted by arrival time within the specified time range.
        
        Args:
            from_seconds (int): Start time in seconds for the time range
            to_seconds (int): End time in seconds for the time range
            
        Returns:
            list: List of Vehicle objects that have more than one junction remaining,
                  sorted by arrival time within the specified range
        """
        res = []
        vehicles = self.get_list_of_vehicles_sorted_by_arrival_time_from_and_to_seconds(from_seconds, to_seconds)
        for vehicle in vehicles:
            if not vehicle.is_next_lane_the_final_lane():
                res.append(vehicle)
        return res

    def get_list_of_vehicles_sorted_by_arrival_time_from_and_to_seconds(self, from_seconds, to_seconds):
        """
        Get a list of vehicles sorted by their arrival time within the specified time range.
        
        Args:
            from_seconds (int): Start time in seconds for the time range
            to_seconds (int): End time in seconds for the time range
            
        Returns:
            list: List of Vehicle objects sorted by arrival time within the specified range
            
        Note:
            This method filters vehicles based on their distance from the next junction
            and sorts them by arrival time. The commented code shows the original implementation
            that was replaced with a more efficient lambda-based sorting approach.
        """
        return sorted(self.vehicles, key=lambda obj: getattr(obj, "is_away_from_next_junction_by_between_start_and_end_seconds")(from_seconds, to_seconds))

    def vehicle_enter_lane(self, vehicle):
        """
        Add a vehicle to this road lane.
        
        Args:
            vehicle (Vehicle): The vehicle object to add to this lane
            
        Returns:
            bool: True if the vehicle was successfully added, False otherwise
            
        Note:
            The vehicle's current road lane and length attributes are automatically updated
            to reflect its new position on this lane.
        """
        if not isinstance(vehicle, Vehicle):
            return False

        vehicle.cur_road_lane = self
        vehicle.cur_road_lane_length = self.length
        self.vehicles.append(vehicle)
        self.vehicles_size += 1
        return True

    def vehicle_leave_lane(self, vehicle):
        """
        Remove a vehicle from this road lane.
        
        Args:
            vehicle (Vehicle): The vehicle object to remove from this lane
            
        Returns:
            bool: True if the vehicle was successfully removed, False if not found
            
        Note:
            The vehicle's current road lane attribute is automatically set to None
            when it leaves the lane.
        """
        if not isinstance(vehicle, Vehicle):
            return False
        for v in self.vehicles:
            if v is vehicle:
                vehicle.cur_road_lane = None
                self.vehicles.remove(vehicle)
                self.vehicles_size -= 1
                return True
        return False
