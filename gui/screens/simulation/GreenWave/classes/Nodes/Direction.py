from classes.Nodes.Lane import Lane
from functions import find_obj_index_in_array
from classes.Enums.LaneFacing import LaneFacing


def check_possible_collision(left_lane, right_lane):
    if (left_lane.to_lanes[0]) < (right_lane.to_lanes[-1]):
        raise TypeError("Direction is invalid: Possible collision between different lanes")


def check_direction_validity(lanes):  # lanes: list[Lane]
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

    def __init__(self, index_in_map, in_lanes=None, out_lanes=None):  # in_lanes: list[Lane], out_lanes: list[Lane]
        self.in_lanes = []  # the logical order is from the right to the left
        self.out_lanes = []  # the logical order is from the right to the left
        self.in_size = 0
        self.out_size = 0
        self.size = 0
        self.parent_junction = None
        self.index_in_map = index_in_map

        if None is not in_lanes:
            try:
                check_direction_validity(in_lanes)
                self.in_lanes = in_lanes
                self.in_size = len(in_lanes)
                self.size += self.in_size
                self.__set_lanes(in_lanes)
            except TypeError as e:
                print(f"Direction couldn't be created due to this error: {e}")

        if None is not out_lanes:
            try:
                check_direction_validity(out_lanes)
                self.out_lanes = out_lanes
                self.out_size = len(out_lanes)
                self.size += self.out_size
                self.__set_lanes(out_lanes)
            except TypeError as e:
                print(f"Direction couldn't be created due to this error: {e}")

    def __set_lanes(self, lanes):
        for lane in lanes:
            lane.set_parent_direction(self)

    def set_parent_junction(self, parent_junction):  # parent_junction: Junction
        self.parent_junction = parent_junction

    def add_to_left(self, lane):  # lane: Lane
        if LaneFacing.IN == lane.facing:
            self.in_lanes.append(lane)
            self.in_size += 1
            self.size += 1
            return True
        elif LaneFacing.OUT == lane.facing:
            self.out_lanes.append(lane)
            self.out_size += 1
            self.size += 1
            return True
        return False

    def add_to_right(self, lane):  # lane: Lane
        if LaneFacing.IN == lane.type:
            self.in_lanes.insert(0, lane)
            self.in_size += 1
            self.size += 1
            return True
        elif LaneFacing.OUT == lane.type:
            self.out_lanes.insert(0, lane)
            self.out_size += 1
            self.size += 1
            return True
        return False

    def find_index_by_lane(self, lane):  # lane: Lane
        if not isinstance(lane, Lane):
            return None
        if LaneFacing.IN == lane.facing:
            return find_obj_index_in_array(lane, self.in_lanes)
        elif LaneFacing.OUT == lane.facing:
            return find_obj_index_in_array(lane, self.out_lanes)
        return None

    def set_lane_as_direction_tuple(self, lane, index):  # lane: tuple[Direction], index: int
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
        """
        if None is self.index_in_junction:
            return None
        res = f"Direction {self.index_in_junction}:\nIn Lanes:\n"
        """
        res = f"Direction:\nIn Lanes:\n"
        for lane in self.in_lanes:
            res += f"\t\t{lane}\n"
        res += "\nOut Lanes:\n"
        for lane in self.out_lanes:
            res += f"\t\t{lane}\n"
        return res
