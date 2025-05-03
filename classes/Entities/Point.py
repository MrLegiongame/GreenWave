from abc import ABC, abstractmethod
import math


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
        return math.sqrt((point.x - self.x) ** 2 + (point.y - self.y) ** 2)

    def set_point(self, x, y):
        self.x = x
        self.y = y

    def get_point(self):
        return self.x, self.y
