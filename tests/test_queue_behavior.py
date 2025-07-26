#!/usr/bin/env python3
"""
Test script to verify queue behavior and identify the issue with vehicle queue management
"""

import sys
import os
import time
import pygame

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classes.Nodes.Lane import Lane
from classes.Entities.Vehicles.Vehicle import Vehicle
from classes.Entities.Point import Point
from classes.Nodes.Junction import Junction
from classes.Enums.LaneFacing import LaneFacing
from classes.Enums.State import State

pygame.init()
dummy_surface = pygame.Surface((10, 10), pygame.SRCALPHA)

def test_queue_behavior():
    """Test the queue behavior to identify the issue"""
    
    # Create a test lane
    lane = Lane(LaneFacing.IN)
    lane.set_cur_state(State.GREEN)
    
    # Create mock vehicles
    vehicles = []
    for i in range(3):
        start_point = Point(0, 0)
        end_point = Point(100, 100)
        start_junction = Junction()  # Create empty junction
        start_junction.set_point(start_point)
        start_junction.junction_index = i
        end_junction = Junction()  # Create empty junction
        end_junction.set_point(end_point)
        end_junction.junction_index = i + 10
        
        vehicle = Vehicle(
            length=4.5,
            weight=1500,
            start_node=start_junction,
            end_node=end_junction,
            vehicle_type="Car",
            energy_type="Electric",
            maximum_speed=120
        )
        vehicles.append(vehicle)
    
    print("=== Testing Queue Behavior ===")
    
    # Add vehicles to queue in order
    for i, vehicle in enumerate(vehicles):
        print(f"\nAdding vehicle {vehicle.vehicle_id} to queue (should be position {i})")
        lane.add_to_queue(vehicle)
        print(f"Queue after addition: {[v.vehicle_id for v in lane.vehicles_queue]}")
    
    # Test queue position checking
    print(f"\n=== Queue Position Check ===")
    for vehicle in vehicles:
        position = lane.get_vehicle_queue_position(vehicle)
        print(f"Vehicle {vehicle.vehicle_id} is at position {position}")
    
    # Test processing vehicles in order
    print(f"\n=== Processing Vehicles ===")
    while lane.vehicles_queue:
        first_vehicle = lane.vehicles_queue[0]
        print(f"Processing vehicle {first_vehicle.vehicle_id} (should be first)")
        removed_vehicle = lane.pop_head_from_queue()
        print(f"Removed vehicle {removed_vehicle.vehicle_id}")
        print(f"Queue after removal: {[v.vehicle_id for v in lane.vehicles_queue]}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_queue_behavior() 