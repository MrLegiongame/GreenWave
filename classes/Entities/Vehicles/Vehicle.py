"""
Vehicle Module

This module contains the Vehicle abstract base class and related logging functionality
for managing vehicles in the traffic simulation system. The Vehicle class represents
individual vehicles with properties like position, speed, energy consumption, and
pollution emissions.

Classes:
    Vehicle: Abstract base class for vehicles with movement, energy, and pollution tracking.

Functions:
    log_vehicle_event: Log vehicle events to a debug log file.
"""

import math
import os
import random
import threading
import time
from abc import ABC
from classes.Entities.Point import Point
import pygame

from classes.Enums.LaneFacing import LaneFacing
from classes.Enums.State import State

LOG_PATH = os.path.join(os.path.dirname(__file__), '../logs/vehicle_debug.log')

def log_vehicle_event(msg):
    """
    Log vehicle events to a debug log file.
    
    Args:
        msg (str): The message to log
        
    Note:
        Creates the log directory if it doesn't exist and appends the message
        to the vehicle debug log file with UTF-8 encoding.
    """
    log_dir = os.path.dirname(LOG_PATH)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')


class Vehicle(ABC):
    """
    Abstract base class for vehicles in the traffic simulation system.
    
    The Vehicle class represents individual vehicles with comprehensive tracking
    of movement, energy consumption, pollution emissions, and statistical data.
    Each vehicle has a unique ID and maintains its own path through the traffic
    network, including current position, speed, and destination information.
    
    Attributes:
        vehicle_id (int): Unique identifier for this vehicle
        length (float): Length of the vehicle in meters
        weight (float): Weight of the vehicle in kilograms
        start_node (Junction): Starting junction
        end_node (Junction): Destination junction
        start_point (Point): Starting coordinates
        end_point (Point): Destination coordinates
        cur_road_lane (RoadLane): Current road lane the vehicle is on
        road_lanes (list): List of road lanes in the vehicle's path
        cur_road_lane_length (float): Length of current road lane
        roads_passed (int): Number of roads the vehicle has passed
        cur_point (Point): Current position of the vehicle
        vehicle_type (str): Type of vehicle (e.g., "car", "truck")
        energy_type (str): Type of energy used (e.g., "electric", "gasoline")
        maximum_speed (float): Maximum speed capability in m/s
        velocity (float): Current velocity in m/s
        acceleration (float): Current acceleration in m/s²
        has_reached_destination (bool): Flag indicating if vehicle has reached destination
        distance_on_road_lane (float): Distance traveled on current road lane
        lanes_path (list): List of lanes in the vehicle's path
        roads_path (list): List of road segments in the vehicle's path
        lanes_path_index (int): Current index in the lanes path
        total_time (float): Total time spent in simulation
        total_energy_consumed (float): Total energy consumed in Joules
        total_pollution (float): Total pollution emitted in grams CO2
        total_distance (float): Total distance traveled in kilometers
        stops_count (int): Number of times the vehicle has stopped
        acceleration_events (int): Number of acceleration events
        idle_time (float): Total time spent idle
        creation_time (float): Time when vehicle was created
        last_stop_time (float): Time of last stop
        is_stopped (bool): Flag indicating if vehicle is currently stopped
        last_velocity (float): Previous velocity value for tracking
    """
    
    # Class variable to track the next available vehicle ID
    _next_vehicle_id = 1
    
    def __init__(self, length, weight, start_node, end_node, vehicle_type, energy_type, maximum_speed, acceleration=0):
        """
        Initialize a new Vehicle instance.
        
        Args:
            length (float): Length of the vehicle in meters
            weight (float): Weight of the vehicle in kilograms
            start_node (Junction): Starting junction
            end_node (Junction): Destination junction
            vehicle_type (str): Type of vehicle (e.g., "car", "truck")
            energy_type (str): Type of energy used (e.g., "electric", "gasoline")
            maximum_speed (float): Maximum speed capability in m/s
            acceleration (float, optional): Initial acceleration in m/s². Defaults to 0.
            
        Note:
            Each vehicle gets a unique ID automatically assigned. The vehicle starts
            at the start_node position and will navigate to the end_node through
            the traffic network.
        """
        # Assign unique vehicle ID
        self.vehicle_id = Vehicle._next_vehicle_id
        Vehicle._next_vehicle_id += 1
        
        self.length = length
        self.weight = weight
        self.start_node = None
        self.start_point = None
        self.end_node = None
        self.end_point = None
        self.set_start_and_end_nodes(start_node, end_node)
        self.cur_road_lane = None
        self.road_lanes = None
        self.cur_road_lane_length = 0
        self.roads_passed = 0
        self.cur_point = self.start_point
        self.vehicle_type = vehicle_type
        self.energy_type = energy_type
        self.maximum_speed = maximum_speed
        # self.velocity = min(self.cur_road_lane.maximum_speed, self.maximum_speed)
        self.velocity = None
        self.acceleration = acceleration
        self.has_reached_destination = False  # Add flag for destination arrival

        self.distance_on_road_lane = 0
        self.lanes_path = []
        self.roads_path = []
        self.lanes_path_index = 0
        self.__end_in_lane = None
        self.__last_lane = None
        self.__lanes_passed = 0
        self.__last_distance_to_next_junction = None
        self.__last_move_time_stamp = None
        self.from_junction = None
        self.to_junction = None

        # Stats
        self.total_time = 0
        self.total_energy_consumed = 0
        self.total_pollution = 0
        self.total_distance = 0
        
        # Additional tracking parameters for statistics
        self.stops_count = 0
        self.acceleration_events = 0
        self.idle_time = 0
        self.creation_time = None
        self.last_stop_time = None
        self.is_stopped = False
        self.last_velocity = 0

        print(
            f"[Vehicle Init] Vehicle #{self.vehicle_id} - {vehicle_type} with {energy_type} created from {self.start_point} "
            f"to {self.end_point}")
        print(f"[Vehicle Init] Vehicle #{self.vehicle_id} - cur_point: {self.cur_point}")

    def is_next_lane_the_final_lane(self):  # architecture due to multithreading
        """
        Check if the next lane in the path is the final destination lane.
        
        Returns:
            bool: True if the next lane is the final lane, False otherwise
            
        Note:
            This method is designed to handle multithreading scenarios where
            the lanes_passed counter might be accessed concurrently.
        """
        lanes_passed = self.__lanes_passed + 1
        if lanes_passed >= len(self.lanes_path):
            return True
        # Check if the next lane is the designated end lane
        return self.__end_in_lane is self.lanes_path[lanes_passed]

    def set_start_and_end_nodes(self, start, end):
        """
        Set the start and end nodes and their corresponding points.
        
        Args:
            start (Junction): Starting junction
            end (Junction): Destination junction
        """
        self.start_node = start
        self.start_point = start.point
        self.end_node = end
        self.end_point = end.point

    def adapt_lanes_path_to_match_out_lanes_to_in_lanes(self):
        """
        Adapt the lanes path to ensure proper connection between out lanes and in lanes.
        
        This method modifies the lanes_path to ensure that out lanes properly
        connect to their corresponding in lanes in the traffic network.
        """
        for index in range(0, len(self.lanes_path), 2):
            self.lanes_path[index] = self.lanes_path[index+1].road_lane.source_lane

    def set_path(self, graph):
        """
        Set the vehicle's path through the traffic network.
        
        Args:
            graph (Graph): The traffic network graph for pathfinding
            
        Note:
            This method finds a path from the start node to the end node using
            the graph's pathfinding capabilities. If no direct path is found,
            it attempts to find alternative paths or creates a minimal path.
            The method also sets up the road_lanes list and initializes the
            vehicle's current position on the first road lane.
        """
        start_out_lane = None
        end_in_lane = None

        start_directions = self.start_node.directions.copy()
        while not start_out_lane:
            random_index = random.randrange(len(start_directions))
            if start_directions[random_index].out_lanes:
                start_out_lane = random.choice(start_directions[random_index].out_lanes)
            else:
                start_directions.pop(random_index)

        end_directions = self.end_node.directions.copy()
        while not end_in_lane:
            random_index = random.randrange(len(end_directions))
            if end_directions[random_index].in_lanes:
                end_in_lane = random.choice(end_directions[random_index].in_lanes)
            else:
                end_directions.pop(random_index)

        self.lanes_path, self.roads_path = graph.get_path(start_out_lane, end_in_lane)

        # If no path is found, try to find a path to a nearby junction
        if (not self.lanes_path) or (not self.roads_path):
            print(f"No path available between {start_out_lane} and {end_in_lane}, trying to find alternative path...")
            # Try to find a path to the next junction
            end_in_lane = start_out_lane.road_lane.destination_lane
            self.lanes_path, self.roads_path = graph.get_path(start_out_lane, end_in_lane)

            # If still no path, create a minimal path
            if (not self.lanes_path) or (not self.roads_path):
                print("No alternative path found, creating minimal path...")
                self.lanes_path = [start_out_lane, end_in_lane]
                self.roads_path = [(start_out_lane, end_in_lane)]

        print(f"Final path: {self.roads_path}")

        self.__end_in_lane = end_in_lane

        self.road_lanes = []
        for lane1, lane2 in self.roads_path:
            if LaneFacing.IN == lane1.facing and LaneFacing.OUT == lane2.facing:
                in_lane = lane1
                out_lane = lane2
            elif LaneFacing.OUT == lane1.facing and LaneFacing.IN == lane2.facing:
                in_lane = lane2
                out_lane = lane1
            else:
                raise TypeError("set_path method is invalid: Invalid order in path: Lane with facing equals to None")
            self.road_lanes.append(graph.find_road_lanes_by_lanes(in_lane=in_lane))

        if not self.road_lanes:
            print("Warning: No road lanes found for path")
            return

        self.adapt_lanes_path_to_match_out_lanes_to_in_lanes()

        self.cur_road_lane = self.road_lanes[self.roads_passed]
        self.cur_road_lane_length = self.cur_road_lane.parent_road.length
        self.__last_lane = self.lanes_path[self.__lanes_passed]
        print(f"set_path path len: {len(self.lanes_path)}")
        self.__lanes_passed += 1
        print(f"[DEBUG] SET PATH After increment __lanes_passed={self.__lanes_passed}")

    def get_cur_lane(self):
        """
        Get the current lane the vehicle is on.
        
        Returns:
            Lane: The current lane object
        """
        return self.__last_lane

    def get_next_lane(self):
        """
        Get the next lane in the vehicle's path.
        
        Returns:
            Lane or None: The next lane, or None if at the end of the path
        """
        if self.__lanes_passed >= len(self.lanes_path):
            return None
        return self.lanes_path[self.__lanes_passed]

    def get_source_junction(self):
        """
        Get the source junction the vehicle is coming from.
        
        Returns:
            Junction: The source junction
        """
        return self.from_junction

    def get_destination_junction(self):
        """
        Get the destination junction the vehicle is heading to.
        
        Returns:
            Junction or None: The destination junction, or None if at the end of the path
        """
        if self.__lanes_passed > len(self.lanes_path) + 1:
            return None
        return self.to_junction

    def __is_passed_junction(self):
        """
        Check if the vehicle has passed the current junction.
        
        This method determines if the vehicle has moved far enough along the
        current road to be considered as having passed the junction.
        
        Returns:
            bool: True if the vehicle has passed the junction, False otherwise
            
        Raises:
            Exception: If there's an error accessing the lanes path
        """
        try:
            next_junc = self.lanes_path[self.__lanes_passed].parent_junction.point
            self.to_junction = self.lanes_path[self.__lanes_passed].parent_junction
            # print(f"[__is_passed_junction] next_junction={next_junc.get_point()}")
        except Exception as e:
            # print(f"[__is_passed_junction] ERROR accessing lanes_path[{self.__lanes_passed}]: {e}")
            raise

        current_pt = self.cur_point.get_point()

        # Calculate distance along the road path
        self.from_junction = self.__last_lane.parent_junction
        self.from_node = self.from_junction.point
        self.to_node = next_junc
        road_length = self.cur_road_lane.parent_road.length
        pixel_length = self.from_node.get_distance_from_point(self.to_node)
        # print(f"__is_passed_junction path len: {len(self.lanes_path)}")
        # Calculate how far along the road we are
        current_distance = self.cur_point.get_distance_from_point(self.from_node)
        total_distance = self.from_node.get_distance_from_point(self.to_node)
        progress = current_distance / total_distance if total_distance > 0 else 0

        # print(f"[__is_passed_junction] current_point={current_pt}, progress={progress:.2f}, total_distance={total_distance:.2f}")

        passed = False
        if self.__last_distance_to_next_junction is not None:
            passed = progress > 0.99
            # print(f"[__is_passed_junction] passed={passed} (progress > 0.95: {progress > 0.95})")

        if passed:
            print(
                f"[__is_passed_junction] passed={passed}, setting __last_distance_to_next_junction={current_distance}")
        return passed

    def setup_move(self):
        """
        Set up the vehicle for movement by initializing necessary parameters.
        
        This method initializes the vehicle's movement parameters including
        creation time, move timestamp, current lane, velocity, and distance
        tracking. It ensures the vehicle is properly positioned and ready
        for movement in the traffic simulation.
        
        Note:
            This method is called before each move operation to ensure
            all necessary parameters are properly initialized.
        """
        # print(f"[setup_move] Starting with __lanes_passed={self.__lanes_passed}, last_lane={self.__last_lane}")
        if self.creation_time is None:
            self.creation_time = time.time()
            self.track_movement()

        if self.__last_move_time_stamp is None:
            self.__last_move_time_stamp = time.time()

        if self.__last_lane is None:
            try:
                self.__last_lane = self.lanes_path[self.__lanes_passed]
                print(f"Setup path len: {len(self.lanes_path)}")
                self.__lanes_passed += 1
                self.__last_lane.road_lane.vehicle_enter_lane(self)
                # print(f"[setup_move] Set last_lane={self.__last_lane} at __lanes_passed={self.__lanes_passed}")
            except Exception as e:
                print(f"[setup_move] ERROR accessing lanes_path[{self.__lanes_passed}]: {e}")
                raise

        if self.velocity is None:
            self.velocity = min(self.cur_road_lane.parent_road.maximum_speed, self.maximum_speed)
            # print(f"[setup_move] initialized velocity to {self.velocity}")

        if self.__last_distance_to_next_junction is None:
            self.__last_distance_to_next_junction = self.cur_road_lane_length

    def cross_junction(self, from_stop: bool):
        """
        Handle the vehicle crossing through a junction.
        
        This method manages the vehicle's transition from one road lane to another
        when crossing a junction. It handles queue management, timing delays,
        lane transitions, and updates energy/pollution statistics.
        
        Args:
            from_stop (bool): Whether the vehicle is crossing from a stopped position
                             (in a queue) or moving freely
                             
        Note:
            This method is typically called in a separate thread to handle
            the timing delays associated with crossing junctions. It updates
            the vehicle's position, lane assignments, and consumption statistics.
        """
        try:
            log_vehicle_event(f"[cross_junction] Vehicle #{self.vehicle_id} | from_stop={from_stop} | __lanes_passed={self.__lanes_passed} | __last_lane={self.__last_lane} | queue={getattr(self.__last_lane, 'vehicles_queue', None)}")
            if from_stop:
                # Get timing delay from queue and wait before crossing
                vehicle, time_to_sleep = self.__last_lane.pop_head_from_queue()
                log_vehicle_event(f"[cross_junction] Vehicle #{self.vehicle_id} popped from queue, sleeping {time_to_sleep:.2f}s")
                time.sleep(time_to_sleep)
                self.__last_lane.free_to_leave_queue = True
                self.track_movement()
                log_vehicle_event(f"[cross_junction] Vehicle #{self.vehicle_id} set free_to_leave_queue=True after crossing from stop.")

            # Fix: Prevent IndexError by checking bounds
            if self.__lanes_passed >= len(self.lanes_path):
                if self.get_queue_position() == 0:
                    self.__last_lane.pop_head_from_queue()
                    log_vehicle_event(f"[cross_junction] Vehicle #{self.vehicle_id} popped from queue at end of path.")
                self.has_reached_destination = True
                self.__last_lane.free_to_leave_queue = True
                log_vehicle_event(f"[cross_junction] Vehicle #{self.vehicle_id} has reached destination. Exiting cross_junction.")
                return

            # Progress to next lane in path
            self.roads_passed += 1
            self.__last_lane = self.lanes_path[self.__lanes_passed]
            self.__lanes_passed += 1
            self.__last_lane.road_lane.vehicle_enter_lane(self)
            self.cur_road_lane = self.road_lanes[self.roads_passed]
            self.cur_road_lane_length = self.cur_road_lane.parent_road.length
            self.__last_distance_to_next_junction = self.cur_road_lane_length
            # Set velocity to road or vehicle maximum, whichever is lower
            self.velocity = min(self.cur_road_lane.parent_road.maximum_speed, self.maximum_speed)
            log_vehicle_event(f"[cross_junction] Vehicle #{self.vehicle_id} entered new lane: {self.__last_lane}")

            if from_stop:
                # Calculate energy and pollution for acceleration from stop
                to_velocity = min(self.__last_lane.road_lane.parent_road.maximum_speed, self.maximum_speed)
                self.total_energy_consumed += self.get_energy_consumption_to_velocity(to_velocity)
                self.total_pollution += self.get_pollution_to_velocity(to_velocity)
                log_vehicle_event(f"[cross_junction] Vehicle #{self.vehicle_id} updated energy={self.total_energy_consumed}, pollution={self.total_pollution}")
        except Exception as e:
            log_vehicle_event(f"[cross_junction][EXCEPTION] Vehicle #{self.vehicle_id}: {e}")

    def move(self, dt):
        """
        Move the vehicle for the given time delta.
        
        This method handles the vehicle's movement logic, including lane transitions,
        junction crossing, queue management, and position updates. It processes
        different lane types (IN/OUT) and manages traffic light interactions.
        
        Args:
            dt (float): Time delta in hours (converted from milliseconds)
            
        Note:
            The method handles different scenarios:
            - IN lanes: Queue management and traffic light waiting
            - OUT lanes: Movement along roads and junction crossing
            - Destination arrival: Final lane processing
            - Energy and pollution tracking during movement
        """
        dt = dt / 3_600.0  # Convert milliseconds to hours
        self.setup_move()

        if self.__lanes_passed >= len(self.lanes_path):
            if self.get_queue_position() == 0:
                self.has_reached_destination = True
                self.__last_lane.pop_head_from_queue()
                log_vehicle_event(f"[move] Vehicle #{self.vehicle_id} popped from queue at end of path.")
            return

        if self.__last_lane.facing == LaneFacing.IN:
            log_vehicle_event(
                f"[move] Vehicle #{self.vehicle_id} | __lanes_passed={self.__lanes_passed} | __last_lane={self.__last_lane} | queue={getattr(self.__last_lane, 'vehicles_queue', None)}")

            if self.__last_lane is self.__end_in_lane:
                return
            try:
                # Check if vehicle is at front of queue and can proceed
                at_front = (self.__last_lane.vehicles_queue != [] and self is self.__last_lane.vehicles_queue[0])
                lane_green = self.__last_lane.cur_state in [State.GREEN, State.GREEN_FLICKERING]
                free_to_leave = self.__last_lane.free_to_leave_queue
                log_vehicle_event(f"[move] Vehicle #{self.vehicle_id} IN-lane: at_front={at_front}, lane_green={lane_green}, free_to_leave={free_to_leave}")
                if lane_green and self.__last_lane.vehicles_queue != [] and free_to_leave:
                    if at_front:
                        log_vehicle_event(f"[move] Vehicle #{self.vehicle_id} is at the front of the queue, lane is green, free_to_leave_queue={free_to_leave}. Starting cross_junction thread.")
                        self.__last_lane.free_to_leave_queue = False
                        try:
                            # Start crossing junction in separate thread to handle timing delays
                            crossing_thread = threading.Thread(target=self.cross_junction, args=(True,))
                            crossing_thread.start()
                            log_vehicle_event(f"[move] Started cross_junction thread for Vehicle #{self.vehicle_id}")
                        except Exception as e:
                            log_vehicle_event(f"[move][EXCEPTION] Vehicle #{self.vehicle_id} when starting thread: {e}")
            except Exception as e:
                log_vehicle_event(f"[move][EXCEPTION] Vehicle #{self.vehicle_id} in IN-lane logic: {e}")
                raise
            self.__last_move_time_stamp = time.time()
            self.update_total_time()
            return

        elif self.__last_lane.facing == LaneFacing.OUT:
            if self.__is_passed_junction():
                try:
                    self.__last_lane.road_lane.vehicle_leave_lane(self)
                    if self.__lanes_passed > len(self.lanes_path):
                        self.__lanes_passed -= 1
                    self.__last_lane = self.lanes_path[self.__lanes_passed]
                    self.__lanes_passed += 1
                    log_vehicle_event(f"[move] Vehicle #{self.vehicle_id} OUT-lane: After increment __lanes_passed={self.__lanes_passed}")
                except Exception as e:
                    log_vehicle_event(f"[move][EXCEPTION] Vehicle #{self.vehicle_id} in OUT-lane logic: {e}")
                    raise
                if self.__last_lane is not self.__end_in_lane:
                    lane_green = self.__last_lane.cur_state in [State.GREEN, State.GREEN_FLICKERING]
                    free_to_leave = self.__last_lane.free_to_leave_queue
                    at_front = (self.__last_lane.vehicles_queue != [] and self is self.__last_lane.vehicles_queue[0])
                    log_vehicle_event(f"[move] Vehicle #{self.vehicle_id} OUT-lane: at_front={at_front}, lane_green={lane_green}, free_to_leave={free_to_leave}")
                    if self.__last_lane.vehicles_queue == [] and lane_green and free_to_leave:
                        log_vehicle_event(f"[move] Vehicle #{self.vehicle_id} can cross junction without queue. Calling cross_junction.")
                        self.cross_junction(False)
                    else:
                        self.__last_lane.add_to_queue(self)
                        self.track_stop()
                        if at_front:
                            log_vehicle_event(f"[move] Vehicle #{self.vehicle_id} is at the front of the queue, lane is green, free_to_leave_queue={free_to_leave}. Waiting for green.")
                new_x, new_y = self.__last_lane.parent_junction.point.get_point()
            else:
                self.to_junction = self.lanes_path[self.__lanes_passed].parent_junction
                self.from_junction = self.lanes_path[self.__lanes_passed - 1].parent_junction
                from_node = self.lanes_path[self.__lanes_passed - 1].parent_junction.point
                to_node = self.lanes_path[self.__lanes_passed].parent_junction.point
                distance = self.velocity * dt + 0.5 * self.acceleration * (dt ** 2)
                road_length = self.cur_road_lane.parent_road.length
                pixel_length = from_node.get_distance_from_point(to_node)
                length = (distance * pixel_length) / road_length
                alpha = from_node.get_slope_angle_in_rad(to_node)
                dx = length * math.cos(alpha)
                dy = length * math.sin(alpha)
                new_x = self.cur_point.x + dx
                new_y = self.cur_point.y + dy
                self.track_acceleration(self.acceleration)
                
                # Update distance traveled
                self.total_distance += distance
                if self.__last_distance_to_next_junction - distance >= 0:
                    self.__last_distance_to_next_junction -= distance
                else:
                    self.__last_distance_to_next_junction = 0
                
                self.total_energy_consumed += self.calculate_energy_consumption(distance)
                self.total_pollution += self.calculate_pollution(distance)
        else:
            raise TypeError("move method is invalid: Invalid order in path: facing is None")
        self.update_total_time()
        self.cur_point = Point(new_x, new_y)
        self.__last_move_time_stamp = time.time()
        if self.__lanes_passed >= len(self.lanes_path):
            return
        try:
            # Calculate remaining distance to next junction for timing estimates
            nxt = self.lanes_path[self.__lanes_passed].parent_junction.point
            last_junction_point = self.__last_lane.parent_junction.point
            if last_junction_point.get_distance_from_point(nxt) != 0:
                # Convert pixel distance to road distance for accurate timing
                dist = self.cur_point.get_distance_from_point(nxt) * self.cur_road_lane_length / last_junction_point.get_distance_from_point(nxt)
                # self.__last_distance_to_next_junction = dist  # in km
        except Exception as e:
            log_vehicle_event(f"[move][EXCEPTION] Vehicle #{self.vehicle_id} in distance calc: {e}")
            raise
        # Update velocity using physics: v = u + at
        self.velocity += self.acceleration * dt

    def __lt__(self, other):
        """
        Compare vehicles based on time to next junction.
        
        Args:
            other (Vehicle): Another vehicle to compare with
            
        Returns:
            bool: True if this vehicle reaches the next junction before the other
        """
        return self.get_time_to_next_junction_in_sec() < other.get_time_to_next_junction_in_sec()

    def get_time_to_next_junction_in_sec(self):
        """
        Calculate the time in seconds until the vehicle reaches the next junction.
        
        Returns:
            float: Time in seconds to reach the next junction
        """
        return (self.__last_distance_to_next_junction / self.velocity) * 3600.0

    def is_away_from_next_junction_by_between_start_and_end_seconds(self, start, end):
        """
        Check if the vehicle is within a specific time range from the next junction.
        
        Args:
            start (float): Start time in seconds
            end (float): End time in seconds
            
        Returns:
            bool: True if the vehicle is within the specified time range from the junction
        """
        if LaneFacing.IN == self.__last_lane.facing:
            return False
        time = self.get_time_to_next_junction_in_sec()
        return end - 0.01 > time > start + 0.01

    def get_energy_consumption_to_velocity(self, to_velocity):
        """
        Calculate the kinetic energy required to reach a target velocity.
        
        Args:
            to_velocity (float): Target velocity in km/h
            
        Returns:
            float: Kinetic energy in Joules
        """
        return 0.5 * self.weight * ((to_velocity / 3.6) ** 2)

    def get_pollution_to_velocity(self, to_velocity):
        """
        Calculate the CO2 pollution emitted to reach a target velocity.
        
        Args:
            to_velocity (float): Target velocity in km/h
            
        Returns:
            float: CO2 emissions in grams
        """
        if "Electric" == self.energy_type:
            return 0
        energy_densities = {
            "Gasoline": 34.2,
            "Gas": 38.6
        }
        emission_factors = {
            "Gasoline": 2310,
            "Gas": 2680
        }
        fuel_in_liters = self.get_energy_consumption_to_velocity(to_velocity) / (0.25 * energy_densities[self.energy_type] * 1_000_000.0)
        return emission_factors[self.energy_type] * fuel_in_liters

    def __str__(self):
        """
        String representation of the vehicle's current position.
        
        Returns:
            str: String showing the vehicle's current coordinates
        """
        return f"(x, y) = {self.get_cur_point().get_point()}"

    def get_cur_point(self):
        """
        Get the vehicle's current position.
        
        Returns:
            Point: Current position of the vehicle
        """
        return self.cur_point

    def has_arrived(self):
        """Check if the vehicle has reached its destination."""
        if self.has_reached_destination:
            return True
            
        # Check if we're at the end of the path and in the final lane
        if self.__lanes_passed >= len(self.lanes_path) or self.__last_lane == self.__end_in_lane:
            # Check if we're close enough to the end point
            if self.cur_point and self.end_point:
                self.has_reached_destination = True
                return True
        return False


    def get_queue_position(self):
        """Get the vehicle's position in its current lane's queue.
        
        Returns:
            int: Position in queue (0-indexed, where 0 is the front of the queue), 
                 or -1 if the vehicle is not in a queue
        """
        if self.__last_lane is None:
            return -1
            
        try:
            # Check if vehicle is in the current lane's queue
            if hasattr(self.__last_lane, 'vehicles_queue') and self in self.__last_lane.vehicles_queue:
                return self.__last_lane.vehicles_queue.index(self)
            else:
                return -1
        except (AttributeError, ValueError):
            return -1

    def get_consumption_summary(self):
        """Get a summary of the vehicle's consumption and pollution statistics.
        
        Returns:
            dict: Dictionary containing consumption and pollution statistics
        """
        return {
            "total_energy_consumed": self.total_energy_consumed / 1_000_000.0,  # in Megajoule
            "total_pollution": self.total_pollution / 1_000.0,  # CO2 in Kg
            "total_distance": self.total_distance,  # in Km
            "total_time": self.total_time,  # in seconds
            "stops_count": self.stops_count,
            "acceleration_events": self.acceleration_events,
            "idle_time": self.idle_time,
            "vehicle_id": self.vehicle_id,
            "vehicle_type": self.vehicle_type,
            "energy_type": self.energy_type
        }

    def track_stop(self):
        """
        Track when vehicle stops due to traffic lights or queues.
        
        This method records when a vehicle comes to a stop, updating
        the stop count and recording the stop time for idle time calculations.
        """
        if not self.is_stopped:
            self.is_stopped = True
            self.last_stop_time = time.time()
            self.stops_count += 1
            print(f"[Vehicle #{self.vehicle_id}] Stopped - Total stops: {self.stops_count}")

    def track_movement(self):
        """
        Track when vehicle starts moving again after being stopped.
        
        This method records when a vehicle resumes movement, calculating
        the idle time spent while stopped and updating the movement status.
        """
        if self.is_stopped:
            self.is_stopped = False
            if self.last_stop_time:
                self.idle_time += time.time() - self.last_stop_time
                print(f"[Vehicle #{self.vehicle_id}] Resumed movement - Idle time: {self.idle_time:.2f}s")

    def track_acceleration(self, current_acceleration):
        """
        Track acceleration events for statistical analysis.
        
        Args:
            current_acceleration (float): Current acceleration value
            
        Note:
            This method counts acceleration events when the vehicle
            transitions from zero or negative acceleration to positive acceleration.
        """
        if current_acceleration > 0 and self.last_velocity <= 0:
            self.acceleration_events += 1
            print(f"[Vehicle #{self.vehicle_id}] Acceleration event - Total: {self.acceleration_events}")
        self.last_velocity = current_acceleration

    def update_total_time(self):
        """
        Update the total time spent in simulation.
        
        This method calculates the total time from vehicle creation
        to the current time for statistical tracking.
        """
        self.total_time = time.time() - self.creation_time

    def calculate_energy_consumption(self, distance_km,
                                C_rr=0.01,
                                C_d=0.3,
                                A=2.2,
                                air_density=1.225,
                                g=9.81):
        """
        Calculate the energy consumption in Joules for driving a given distance.
        
        This method calculates the total energy required to overcome rolling resistance
        and air drag for the specified distance at the vehicle's current velocity.
        
        Args:
            distance_km (float): Distance to travel in kilometers
            C_rr (float, optional): Rolling resistance coefficient. Defaults to 0.01.
            C_d (float, optional): Drag coefficient. Defaults to 0.3.
            A (float, optional): Frontal area in square meters. Defaults to 2.2.
            air_density (float, optional): Air density in kg/m³. Defaults to 1.225.
            g (float, optional): Gravitational acceleration in m/s². Defaults to 9.81.
            
        Returns:
            float: Energy consumption in Joules
            
        Note:
            The calculation includes both rolling resistance (proportional to weight)
            and air resistance (proportional to velocity squared).
        """
        distance_m = distance_km * 1_000.0  # distance in meters

        # Rolling Resistance
        F_rr = C_rr * self.weight * g

        # Drag or Air Resistance
        F_drag = 0.5 * air_density * C_d * A * (self.velocity / 3.6) ** 2

        # Total force
        F_total = F_rr + F_drag

        energy_joules = F_total * distance_m

        return energy_joules

    def calculate_pollution(self, distance_km):
        """
        calculates the CO2 pollution in Grams for driving distance_km kilometers in the same velocity

        param: distance_km: distance in kilometers
        return: CO2 pollution in Grams
        """
        if "Electric" == self.energy_type:
            return 0
        energy_densities = {
            "Gasoline": 34.2,  # MJ per liter
            "Gas": 38.6  # MJ per liter
        }

        emission_factors = {
            "Gasoline": 2310,  # g CO2 per liter
            "Gas": 2680  # g CO2 per liter
        }

        if self.energy_type not in energy_densities:
            raise ValueError("Fuel type must be either 'Gasoline' or 'Gas'.")

        # calcuates the consumed energy
        energy_j = self.calculate_energy_consumption(distance_km)
        energy_mj = energy_j / 1_000_000.0

        liters_used = energy_mj / energy_densities[self.energy_type]

        emissions_grams = liters_used * emission_factors[self.energy_type]

        return emissions_grams

    @staticmethod
    def print_vehicles_on_map(vehicles):
        """
        Print a summary of all vehicles currently on the map.
        
        This static method provides a formatted output showing the status
        of all vehicles that haven't reached their destination yet.
        
        Args:
            vehicles (list): List of Vehicle objects to display
            
        Note:
            Only vehicles that haven't arrived at their destination are displayed.
            The output includes vehicle ID, type, energy type, current position,
            current lane, and queue position.
        """
        print("\n[VEHICLES ON MAP]")
        for v in vehicles:
            if not v.has_arrived():
                print(f"Vehicle #{v.vehicle_id}: type={v.vehicle_type}, energy={v.energy_type}, cur_point={v.get_cur_point().get_point() if v.get_cur_point() else None}, lane={v.get_cur_lane()}, queue_pos={v.get_queue_position()}")
        print("[END VEHICLES ON MAP]\n")
