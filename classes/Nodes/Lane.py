from classes.Edges.RoadLane import RoadLane
from classes.Entities.Vehicles.Vehicle import Vehicle
from screens.functions import sort_and_remove_duplicates_in_tuple
from classes.Enums.State import State
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
    return True


class Lane:

    """
    Each value in lane(tuple: int) is ment to represent a Direction this lane leads to (at least 1)
    in the Junction (of size n).
    Value 0 means the right-most Direction from our Lane's Direction.
    Each value k<n-1 means the k+1 right-most Direction from our Lane's Direction.
    Value n-1 means our own Direction (we came from), which means a U-Turn.
    """

    def __init__(self, facing, to_lanes=None, index_in_junction=None):  # to_lanes: list[Lane]
        self.to_lanes = []
        self.size = 0
        self.parent_direction = None
        self.parent_junction = None
        self.index_in_junction = index_in_junction
        self.facing = facing
        self.cur_state = None
        self.road_lane = None
        self.vehicles_queue = []

        if None is not to_lanes:
            try:
                self.set_to_lanes(to_lanes)
            except TypeError as e:
                print(f"Lane couldn't be created due to this error: {e}")

    def set_to_lanes(self, to_lanes):  # only for in-facing lanes
        if LaneFacing.IN == self.facing:
            return False
        check_lane_validity(to_lanes)
        # self.to_lanes = sort_and_remove_duplicates_in_tuple(to_lanes)
        self.size = len(self.to_lanes)
        return True

    def set_parent_direction(self, parent_direction):  # parent_direction: Direction
        self.parent_direction = parent_direction
        self.parent_junction = parent_direction.parent_junction

    def set_cur_state(self, cur_state):
        if isinstance(cur_state, State):
            self.cur_state = cur_state

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
            self.vehicles_queue.append(vehicle)

    def pop_head_from_queue(self):
        if None is not self.vehicles_queue:
            return self.vehicles_queue.pop(0)
        return False

    # def __str__(self):
    #     if None is self.index_in_direction:
    #         return None
    #     res = f"Lane {self.index_in_direction}: "
    #     for to_direction in self.directions[:-1]:
    #         if None is not to_direction.index_in_junction:
    #             res += f"{to_direction.index_in_junction}, "
    #
    #     return res + f"{self.directions[-1].index_in_junction}"
