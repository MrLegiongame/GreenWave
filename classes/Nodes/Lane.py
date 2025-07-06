from itertools import count

from classes.Edges.RoadLane import RoadLane
from classes.Entities.Vehicles.Vehicle import Vehicle
from classes.Enums.Color import Color
from screens.functions import sort_and_remove_duplicates_in_tuple
from classes.Enums.State import State, STATE_SIZE
from classes.Enums.LaneFacing import LaneFacing
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
        self.free_to_leave_queue = True

        if None is not to_lanes:
            try:
                self.set_to_lanes(to_lanes)
            except TypeError as e:
                print(f"Lane couldn't be created due to this error: {e}")

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
            time_to_cross = 1
            match vehicle.vehicle_type:
                case "Car":
                    time_to_cross = 2
                case "Bus":
                    time_to_cross = 3
                case "Truck":
                    time_to_cross = 4
            self.vehicles_queue.append(vehicle)
            self.time_to_cross_queue.append(time_to_cross)

    def pop_head_from_queue(self):
        if [] is not self.vehicles_queue and [] is not self.time_to_cross_queue:
            return self.vehicles_queue.pop(0), self.time_to_cross_queue.pop(0)
        return False

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
