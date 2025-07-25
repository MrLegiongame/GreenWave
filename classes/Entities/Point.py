from abc import ABC, abstractmethod
import math
from enum import Enum


class RelativeDirection(Enum):
    UP = 0
    DOWN = 1

class Point(ABC):

    def __init__(self, *args):  # *args = (x, y)   OR   *args = x, y
        if 2 == len(args):
            self.x = args[0]
            self.y = args[1]
        elif 1 == len(args):
            self.x = args[0][0]
            self.y = args[0][1]
        else:
            self.x = None
            self.y = None

    def get_distance_from_point(self, point):
        # print("point.x: " + str(point.x), "self.x: " + str(self.x), "point.y:" + str(point.y), "self.y:" + str(self.y))
        return math.sqrt(float((point.x - self.x) ** 2) + float((point.y - self.y) ** 2))

    def set_point(self, x, y):
        self.x = x
        self.y = y

    def get_point(self):
        return self.x, self.y

    def get_slope(self, destination):
        dy = self.y - destination.y
        dx = self.x - destination.x
        if 0 == dx:  # the slope is vertical
            if destination.y > self.y:
                return RelativeDirection.UP
            else:
                return RelativeDirection.DOWN
        return dy / dx

    def get_slope_angle_in_rad(self, destination):
        slope = self.get_slope(destination)
        if RelativeDirection.UP is slope:
            return math.pi / 2
        elif RelativeDirection.DOWN is slope:
            return 3 * math.pi / 2

        if destination.x > self.x:
            return math.atan(slope)
        return math.atan(slope) + math.pi
