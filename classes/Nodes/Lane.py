"""
Lane Module

This module contains the Lane class and related functions for managing individual
lanes within junctions in the traffic simulation system. A Lane represents a
single traffic lane with queue management, vehicle tracking, and traffic light
state management.

Classes:
    Lane: Represents a single traffic lane with queue and state management.
    
Enums:
    TimeToCross: Enumeration of crossing times for different vehicle types.
    
Functions:
    check_lane_validity: Validates a list of lanes for lane creation.
    get_time_to_cross_by_vehicle_type: Gets crossing time based on vehicle type.
    update_time_to_free_queue: Updates queue release time based on traffic conditions.
"""

import time

from itertools import count

from classes.Edges.RoadLane import RoadLane
from classes.Entities.Vehicles.Vehicle import Vehicle
from classes.Enums.Color import Color
from screens.functions import sort_and_remove_duplicates_in_tuple
from classes.Enums.State import State, STATE_SIZE
from classes.Enums.LaneFacing import LaneFacing
from enum import Enum
import bisect


def check_lane_validity(to_lanes):  # to_lanes: list[Lane]
    """
    Validate a list of lanes for lane creation.
    
    Args:
        to_lanes (list of Lane): The list of destination lanes to validate
        
    Returns:
        bool: True if all lanes are valid for lane creation
        
    Raises:
        TypeError: If the list is invalid, empty, or contains non-Lane objects
    """
    if not isinstance(to_lanes, list):
        raise TypeError("Lane is invalid: Not a list")
    if not len(to_lanes) >= 1:
        raise TypeError("Lane is invalid: No to-lanes")
    for to_lane in to_lanes:
        if not isinstance(to_lane, Lane):
            raise TypeError("Lane is invalid: Non-Lane value")
        if not LaneFacing.OUT == to_lane.facing:
            raise TypeError("Lane is invalid: Non-Out_Lane value")
    return True


def get_time_to_cross_by_vehicle_type(vehicle):
    """
    Get the crossing time for a specific vehicle type.
    
    Args:
        vehicle (Vehicle): The vehicle to get crossing time for
        
    Returns:
        float: The crossing time in seconds for the vehicle type
    """
    match vehicle.vehicle_type:
        case "Car":
            return 2
        case "Bus":
            return 2.5
        case "Truck":
            return 3

    return 2


class Lane:
    static_index = count(0)

    """
    Each value in lane(tuple: int) is ment to represent a Direction this lane leads to (at least 1)
    in the Junction (of size n).
    Value 0 means the right-most Direction from our Lane's Direction.
    Each value k<n-1 means the k+1 right-most Direction from our Lane's Direction.
    Value n-1 means our own Direction (we came from), which means a U-Turn.
    """

    def __init__(self, facing, to_lanes=None, index_in_junction=None):  # to_lanes: list[Lane]
        self.index_in_map = next(self.static_index)

        self.to_lanes = []
        self.size = 0
        self.parent_direction = None
        self.parent_junction = None
        self.index_in_junction = index_in_junction
        self.facing = facing
        self.cur_state = None
        self.road_lane = None

        self.vehicles_queue = []  # used as in FIFO (index 0 is head)
        self.time_to_cross_queue = []  # used as in FIFO (index 0 is head)
        self.free_to_leave_queue = True  # used for scheduling vehicles junction crossings

        if None is not to_lanes:
            try:
                self.set_to_lanes(to_lanes)
            except Exception:
                # Lane couldn't be created
                pass

    # TODO: delete later
    """
    def get_time_to_free_current_queue(self):
        return sum(self.time_to_cross_queue)

    def will_be_there_queue_in_given_seconds_for_to_green(self, given_vehicle, is_now_green):
        seconds = given_vehicle.get_time_to_next_junction_in_sec()  # assuming 3 <= seconds <= 17
        latest_time_queue_will_be_released = self.get_time_to_free_current_queue()  # queue will be held from 0 to time to free current queue at least

        if is_now_green:  # green from 0 seconds
            latest_time_queue_will_be_released += 0  # queue will be held from 0 to time to free current queue at least
        else:  # green from 7 seconds
            latest_time_queue_will_be_released += 7  # queue will be held from 0 to time to free current queue + 7 at least

        for vehicle in self.road_lane.get_list_of_vehicles_which_are_left_with_more_than_one_junction_sorted_by_arrival_time_from_and_to_seconds(0, seconds):
            if vehicle is not given_vehicle:
                
                arrival_time = vehicle.get_time_to_next_junction_in_sec()
                time_to_cross = get_time_to_cross_by_vehicle_type(vehicle)

                if latest_time_queue_will_be_released >= arrival_time:
                    latest_time_queue_will_be_released += time_to_cross
                else:
                    latest_time_queue_will_be_released = arrival_time + time_to_cross

                if latest_time_queue_will_be_released > 17:
                    return latest_time_queue_will_be_released >= seconds

        return latest_time_queue_will_be_released >= seconds
    """

    def set_to_lanes(self, to_lanes):  # only for in-facing lanes
        if LaneFacing.OUT == self.facing:
            return False
        check_lane_validity(to_lanes)
        self.to_lanes = to_lanes
        self.size = len(self.to_lanes)
        return True

    def set_parent_direction(self, parent_direction):  # parent_direction: Direction
        self.parent_direction = parent_direction
        self.parent_junction = parent_direction.parent_junction

    def set_cur_state(self, cur_state):
        if isinstance(cur_state, State):
            self.cur_state = cur_state

    def update_state(self):
        self.cur_state = State((self.cur_state.value + 1) % STATE_SIZE)

    def add_to_lane(self, to_lane):  # lane: Lane
        if isinstance(to_lane, Lane):
            # Insert while maintaining order
            bisect.insort(self.to_lanes, to_lane)
            self.size += 1
            self.facing = LaneFacing.IN

    def set_road_lane(self, road_lane):
        if isinstance(road_lane, RoadLane):
            self.road_lane = road_lane
            return True
        return False

    def add_to_queue(self, vehicle):
        if isinstance(vehicle, Vehicle):
            time_to_cross = get_time_to_cross_by_vehicle_type(vehicle)
            self.road_lane.vehicle_leave_lane(vehicle)
            self.vehicles_queue.append(vehicle)
            self.time_to_cross_queue.append(time_to_cross)

    def pop_head_from_queue(self):
        if [] is not self.vehicles_queue and [] is not self.time_to_cross_queue:
            return self.vehicles_queue.pop(0), self.time_to_cross_queue.pop(0)

        return False

    def is_vehicle_in_queue(self, vehicle):
        """Check if a vehicle is in the queue"""
        return vehicle in self.vehicles_queue

    def get_vehicle_queue_position(self, vehicle):
        """Get the position of a vehicle in the queue (0-based index)"""
        if vehicle in self.vehicles_queue:
            return self.vehicles_queue.index(vehicle)
        return -1

    def get_lane_color(self):
        match self.cur_state:
            case State.RED:
                return Color.RED
            case State.RED_YELLOW:
                return Color.ORANGE
            case State.GREEN:
                return Color.GREEN
            case State.GREEN_FLICKERING:
                return Color.DARK_GREEN
            case State.YELLOW:
                return Color.YELLOW
            case _:
                match self.facing:
                    case LaneFacing.IN:
                        return Color.SKY_BLUE
                    case LaneFacing.OUT:
                        return Color.WHITE
                    case _:
                        return Color.BLACK

    def __str__(self):
        is_in_lane = self.facing == LaneFacing.IN
        res = f"{'IN' if is_in_lane else 'OUT'}-Lane #{self.index_in_map}"
        if is_in_lane:
            res += ", directing to OUT-Lanes: \n\t\t\t"
            for to_lane in self.to_lanes[:-1]:
                res += f"OUT-Lane #{to_lane.index_in_map}, "
            res += f"OUT-Lane #{self.to_lanes[-1].index_in_map}"
        return res
