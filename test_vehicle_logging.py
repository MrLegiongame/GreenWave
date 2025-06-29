#!/usr/bin/env python3
"""
Test script to verify vehicle print logging functionality
"""

import sys
import os
import pygame

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from classes.Entities.Vehicles.Vehicle import Vehicle
from classes.Entities.Point import Point
from classes.Nodes.Junction import Junction

def test_vehicle_logging():
    """Test the vehicle print logging functionality"""
    
    # Create mock nodes for testing
    start_point = Point(0, 0)
    end_point = Point(100, 100)
    
    start_junction = Junction()
    start_junction.set_point(start_point)
    start_junction.junction_index = 0
    end_junction = Junction()
    end_junction.set_point(end_point)
    end_junction.junction_index = 1
    
    # Initialize Pygame
    pygame.init()
    pygame.display.set_mode((1, 1))

    # Create a dummy surface for the image
    dummy_surface = pygame.Surface((10, 10), pygame.SRCALPHA)

    # Create a vehicle instance
    vehicle = Vehicle(
        length=4.5,
        weight=1500,
        start_node=start_junction,
        end_node=end_junction,
        image=dummy_surface,
        vehicle_type="Car",
        energy_type="Electric",
        maximum_speed=120
    )
    
    # Test some logging messages
    vehicle._log_print(f"[TEST] Vehicle : {vehicle.vehicle_id} This is a test message")
    vehicle._log_print(f"[TEST] Vehicle : {vehicle.vehicle_id} Another test message with vehicle ID")
    
    # Test a message that doesn't contain vehicle ID (should not be logged)
    vehicle._log_print("This message should not be logged to the file")
    
    print("Test completed. Check the logs/vehicle_print_log.txt file for the logged messages.")

if __name__ == "__main__":
    test_vehicle_logging() 