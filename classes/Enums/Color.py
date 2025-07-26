"""
Color Definitions Module

This module contains the Color enumeration for defining color values used
throughout the traffic simulation system. Colors are defined as RGB tuples
for use with Pygame and other visualization components.

Classes:
    Color: Enumeration of color values with RGB definitions.

Constants:
    COLOR_SIZE: Total number of available colors.
"""

from enum import Enum


class Color(Enum):
    """
    Enumeration of color values used in the traffic simulation system.
    
    This enum defines a comprehensive set of colors as RGB tuples for use
    in visualization, UI elements, and traffic light states. Colors are
    organized into logical groups: grayscale, primary colors, and accent colors.


    """
    BLACK = (0, 0, 0)
    VERY_DARK_GREY = (50, 50, 50)
    DARK_GREY = (100, 100, 100)
    GREY = (140, 140, 140)
    LIGHT_GREY = (200, 200, 200)
    WHITE = (255, 255, 255)

    RED = (255, 0, 0)
    DARK_RED = (140, 0, 0)
    GREEN = (0, 255, 0)
    DARK_GREEN = (0, 140, 0)
    BLUE = (0, 0, 255)
    DARK_BLUE = (0, 0, 140)
    SKY_BLUE = (100, 180, 255)

    ORANGE = (255, 165, 0)
    YELLOW = (255, 255, 0)


COLOR_SIZE = len(Color)
