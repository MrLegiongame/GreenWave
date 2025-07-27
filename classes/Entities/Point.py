"""
Point Module

This module contains the Point abstract base class and RelativeDirection enum for
managing geometric points in the traffic simulation system. The Point class provides
basic geometric operations including distance calculations, slope computations, and
angle calculations.

Classes:
    Point: Abstract base class for geometric points with mathematical operations.
    
Enums:
    RelativeDirection: Enumeration for relative directions (UP, DOWN).
"""

from abc import ABC, abstractmethod
import math
from enum import Enum


class RelativeDirection(Enum):
    """
    Enumeration for relative directions used in slope calculations.
    
    This enum is used when calculating slopes between points, particularly
    when dealing with vertical lines where the slope is undefined.
    """
    UP = 0
    DOWN = 1


class Point(ABC):
    """
    Abstract base class for geometric points with mathematical operations.
    
    The Point class provides a foundation for representing geometric points
    in 2D space with methods for distance calculations, slope computations,
    and angle calculations. It supports flexible initialization from either
    separate x,y coordinates or a coordinate tuple.
    
    Attributes:
        x (float): The x-coordinate of the point
        y (float): The y-coordinate of the point
    """

    def __init__(self, *args):  # *args = (x, y)   OR   *args = x, y
        """
        Initialize a new Point instance.
        
        Args:
            *args: Either (x, y) as separate arguments or (x, y) as a single tuple
            
        Examples:
            Point(10, 20)      # x=10, y=20
            Point((10, 20))    # x=10, y=20
        """
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
        """
        Calculate the Euclidean distance from this point to another point.
        
        Args:
            point (Point): The target point to calculate distance to
            
        Returns:
            float: The Euclidean distance between the two points
            
        Note:
            Uses the formula: sqrt((x2-x1)² + (y2-y1)²)
        """
        return math.sqrt(float((point.x - self.x) ** 2) + float((point.y - self.y) ** 2))


    def get_point(self):
        """
        Get the coordinates of this point as a tuple.
        
        Returns:
            tuple: (x, y) coordinates of the point
        """
        return self.x, self.y

    def get_slope(self, destination):
        """
        Calculate the slope between this point and a destination point.
        
        Args:
            destination (Point): The destination point
            
        Returns:
            float or RelativeDirection: The slope value, or RelativeDirection.UP/DOWN for vertical lines
            
        Note:
            For vertical lines (dx = 0), returns RelativeDirection.UP if destination is above,
            or RelativeDirection.DOWN if destination is below. For non-vertical lines,
            returns the slope value (dy/dx).
        """
        dy = self.y - destination.y
        dx = self.x - destination.x
        if 0 == dx:  # the slope is vertical
            if destination.y > self.y:
                return RelativeDirection.UP
            else:
                return RelativeDirection.DOWN
        return dy / dx

    def get_slope_angle_in_rad(self, destination):
        """
        Calculate the angle of the slope in radians.
        
        Args:
            destination (Point): The destination point
            
        Returns:
            float: The angle in radians (0 to 2π)
            
        Note:
            The angle is calculated as:
            - π/2 for vertical upward lines
            - 3π/2 for vertical downward lines
            - atan(slope) for lines going right
            - atan(slope) + π for lines going left
        """
        slope = self.get_slope(destination)
        if RelativeDirection.UP is slope:
            return math.pi / 2
        elif RelativeDirection.DOWN is slope:
            return 3 * math.pi / 2

        if destination.x > self.x:
            return math.atan(slope)
        return math.atan(slope) + math.pi
