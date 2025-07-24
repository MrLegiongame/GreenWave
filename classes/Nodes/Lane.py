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

class TimeToCross(Enum):
    CAR = 2,
    BUS = 3,
    TRUCK = 4


def get_time_to_cross_by_vehicle_type(vehicle):
    match vehicle.vehicle_type:
        case "Car":
            return 2
        case "Bus":
            return 2.5
        case "Truck":
            return 3
    return 2


def update_time_to_free_queue(latest_time_queue_will_be_released, arrival_time, time_to_cross, is_to_green, is_to_stay):
    result = latest_time_queue_will_be_released


    if is_to_stay and is_to_green:  # green for 13 seconds

        if latest_time_queue_will_be_released >= arrival_time:
            result += time_to_cross
        else:
            result = arrival_time + time_to_cross

        if result > 13:
            return float("inf")

    elif (not is_to_stay) and is_to_green:  # green in 7 until 13 seconds

        time_to_turn_green = 7

        if time_to_turn_green <= arrival_time and time_to_turn_green <= latest_time_queue_will_be_released:
            if latest_time_queue_will_be_released >= arrival_time: # time_to_turn_green ---> arrival_time ---> latest_time_queue_will_be_released
                result += time_to_cross
            else: # time_to_turn_green ---> latest_time_queue_will_be_released ---> arrival_time
                result = arrival_time + time_to_cross

        elif arrival_time <= time_to_turn_green <= latest_time_queue_will_be_released: # arrival_time ---> time_to_turn_green ---> latest_time_queue_will_be_released
            result += time_to_cross
        elif latest_time_queue_will_be_released <= time_to_turn_green <= arrival_time:  # latest_time_queue_will_be_released ---> time_to_turn_green ---> arrival_time
            return float("inf")  # unreachable due to updating latest_time_queue_will_be_released accoring to to_turn_green group case in will_stop_anyway_in_given_seconds (latest_time_queue_will_be_released >= time_to_turn_green)

        elif arrival_time <= time_to_turn_green and latest_time_queue_will_be_released <= time_to_turn_green:
            # latest_time_queue_will_be_released ---> arrival_time ---> time_to_turn_green
            # arrival_time ---> latest_time_queue_will_be_released ---> time_to_turn_green
            return float("inf")  # unreachable due to updating latest_time_queue_will_be_released accoring to to_turn_green group case in will_stop_anyway_in_given_seconds (latest_time_queue_will_be_released >= time_to_turn_green)

        if result > 13:
            return float("inf")

    elif is_to_stay and (not is_to_green):  # NO green for 17 seconds

        return float("inf")  # unreachable due to will_stop_anyway_in_given_seconds handled in to_stay_red group case in will_be_non_green_in_given_seconds

    else:  # if (not is_to_stay) and (not is_to_green)  # green for 3 seconds

        if latest_time_queue_will_be_released >= arrival_time:
            result += time_to_cross
        else:
            result = arrival_time + time_to_cross

        if result > 3:
            return float("inf")



    return result


def will_be_non_green_in_given_seconds(seconds, is_to_green, is_to_stay):
    if is_to_stay and is_to_green:  # green for 13 seconds
        if seconds > 13:
            return True
    elif (not is_to_stay) and is_to_green:  # green in 7 until 13 seconds
        if seconds > 13 or 7 > seconds:
            return True
    elif is_to_stay and (not is_to_green):  # NO green for 17 seconds
        return True
    else:  # if (not is_to_stay) and (not is_to_green)  # green for 3 seconds
        if seconds > 3:
            return True


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
            except TypeError as e:
                print(f"Lane couldn't be created due to this error: {e}")

    def get_time_to_free_current_queue(self):
        return sum(self.time_to_cross_queue)

    def will_be_there_queue_in_given_seconds(self, seconds, is_to_green, is_to_stay):  # assuming 0 <= seconds <= 13
        latest_time_queue_will_be_released = self.get_time_to_free_current_queue()  # queue will be held from 0 to time to free current queue at least

        if is_to_stay and is_to_green:  # green for 13 seconds
            latest_time_queue_will_be_released += 0  # queue will be held from 0 to time to free current queue at least
        elif (not is_to_stay) and is_to_green:  # green in 7 until 13 seconds
            latest_time_queue_will_be_released += 7  # queue will be held from 0 to time to free current queue + 7 at least
        elif is_to_stay and (not is_to_green):  # NO green for 17 seconds
            latest_time_queue_will_be_released += 17  # queue will be held from 0 to time to free current queue + 17 at least
        else:  # if (not is_to_stay) and (not is_to_green)  # green for 3 seconds
            latest_time_queue_will_be_released += 0  # queue will be held from 0 to time to free current queue at least

        for vehicle in self.road_lane.get_list_of_vehicles_sorted_by_arrival_time_from_and_to_seconds(0, seconds):
            arrival_time = vehicle.get_time_to_next_junction_in_sec()
            time_to_cross = get_time_to_cross_by_vehicle_type(vehicle)
            latest_time_queue_will_be_released = update_time_to_free_queue(latest_time_queue_will_be_released, arrival_time, time_to_cross, is_to_green, is_to_stay)

        return latest_time_queue_will_be_released >= seconds

    def will_stop_or_pass_anyway_in_given_seconds(self, seconds):
        """

        checks reasons to stop after arriving in 'seconds' seconds to this lane.

        reasons to stop:
            non-green light
            existing queue

        :param seconds: exact time in real seconds which right after it's duration - the lane is checked for reasons to stop
        :param is_to_green: to_turn_green or to_stay_green group flag
        :param is_to_stay: to_stay_red or to_stay_green group flag
        :return: (whether or not the lane will be non-green) or (it's queue won't be empty in 'seconds' seconds)
        """
        # if will_be_non_green_in_given_seconds(seconds, is_to_green, is_to_stay):
        #     return True
        # if self.will_be_there_queue_in_given_seconds(seconds, is_to_green, is_to_stay):
        #     return True

        will_pass_anyway = True
        will_stop_anyway = True
        for is_to_green, is_to_stay in ((False, False), (False, True), (True, False), (True, True)):
            queue_existence = self.will_be_there_queue_in_given_seconds(seconds, is_to_green, is_to_stay)
            will_pass_anyway = will_pass_anyway and not queue_existence
            will_stop_anyway = will_stop_anyway and queue_existence

        return will_pass_anyway or will_stop_anyway

    def will_stop_or_pass_due_to_state_in_given_seconds(self, seconds, is_to_green_flag, is_to_stay_flag):
        queue_existence = self.will_be_there_queue_in_given_seconds(seconds, is_to_green_flag, is_to_stay_flag)

        will_stop = queue_existence
        will_pass = not queue_existence

        will_stop_due_to_state = False
        will_pass_due_to_state = False

        for is_to_green, is_to_stay in ((not is_to_green_flag, not is_to_stay_flag), (not is_to_green_flag, is_to_stay_flag), (is_to_green_flag, not is_to_stay_flag)):
            queue_existence = self.will_be_there_queue_in_given_seconds(seconds, is_to_green, is_to_stay)
            if will_stop and not queue_existence:
                will_stop_due_to_state = True
            if will_pass and queue_existence:
                will_pass_due_to_state = True

        return will_stop_due_to_state, will_pass_due_to_state

    def set_to_lanes(self, to_lanes):  # only for in-facing lanes
        if LaneFacing.OUT == self.facing:
            return False
        check_lane_validity(to_lanes)
        # self.to_lanes = sort_and_remove_duplicates_in_tuple(to_lanes)
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

    def get_vehicles_on_their_way_expected_to_arrive_in_less_than_3_seconds(self):
        res = []
        for vehicle in self.road_lane.vehicles:
            if vehicle.is_away_from_next_junction_by_less_than_3_seconds():
                res.append(vehicle)
        return res

    def get_vehicles_on_their_way_expected_to_arrive_between_3_and_7_seconds(self):
        res = []
        for vehicle in self.road_lane.vehicles:
            if vehicle.is_away_from_next_junction_by_between_3_and_7_seconds():
                res.append(vehicle)
        return res

    def get_vehicles_on_their_way_expected_to_arrive_between_7_and_10_seconds(self):
        res = []
        for vehicle in self.road_lane.vehicles:
            if vehicle.is_away_from_next_junction_by_between_7_and_10_seconds():
                res.append(vehicle)
        return res

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

    # def __str__(self):
    #     if None is self.index_in_direction:
    #         return None
    #     res = f"Lane {self.index_in_direction}: "
    #     for to_direction in self.directions[:-1]:
    #         if None is not to_direction.index_in_junction:
    #             res += f"{to_direction.index_in_junction}, "
    #
    #     return res + f"{self.directions[-1].index_in_junction}"
