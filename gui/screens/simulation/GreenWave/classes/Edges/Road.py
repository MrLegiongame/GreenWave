from classes.Edges.RoadLane import RoadLane
from classes.Nodes.Direction import Direction
import math


def check_road_validity(name, first_direction, second_direction, length):  # name: str, first_direction: Direction, second_direction: Direction , length: int
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

    # for one way road

    def __init__(self, name, first_direction, second_direction, length):
        self.name = None
        self.first_direction = None
        self.second_direction = None
        self.length = None
        self.road_lanes_first_direction = []
        self.road_lanes_second_direction = []
        self.lanes_first_direction_size = 0
        self.lanes_second_direction_size = 0
        try:
            check_road_validity(name, first_direction, second_direction, length)
            self.name = name
            self.first_direction = first_direction
            self.second_direction = second_direction
            self.length = length

            self.lanes_first_direction_size = first_direction.out_size  # first_direction.out_size = second_direction.in_size
            for lane in range(self.lanes_first_direction_size):
                self.road_lanes_first_direction.append(RoadLane(self, first_direction, second_direction, length))

            self.lanes_second_direction_size = first_direction.in_size  # first_direction.in_size = second_direction.out_size
            for lane in range(self.lanes_second_direction_size):
                self.road_lanes_second_direction.append(RoadLane(self, second_direction, first_direction, length))
        except TypeError as e:
            print(f"Road couldn't be created due to this error: {e}")

    def get_slope(self):
        dy = self.first_direction.parent_junction.point.get_point()[1] - self.second_direction.parent_junction.point.get_point()[1]
        dx = self.first_direction.parent_junction.point.get_point()[0] - self.second_direction.parent_junction.point.get_point()[0]
        if 0 == dx:  # the slope is vertical
            return None
        return dy / dx

    def get_slope_angle_in_rad(self):
        slope = self.get_slope()
        if None is slope:
            return math.pi / 2
        return math.atan(slope)

    def get_slope_angle_in_deg(self):
        rad = self.get_slope_angle_in_rad()
        return rad * 180 / math.pi

    def get_first_point(self):
        if None is not self.first_direction:
            if None is not self.first_direction.parent_junction:
                if None is not self.first_direction.parent_junction.point:
                    return self.first_direction.parent_junction.point.get_point()

    def get_second_point(self):
        if None is not self.second_direction:
            if None is not self.second_direction.parent_junction:
                if None is not self.second_direction.parent_junction.point:
                    return self.second_direction.parent_junction.point.get_point()
