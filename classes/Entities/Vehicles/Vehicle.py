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
    log_dir = os.path.dirname(LOG_PATH)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')


def get_image_list(folder_path):
    supported_exts = (".png", ".jpg", ".jpeg", ".jfif", ".webp")
    return [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.lower().endswith(supported_exts)
    ]


class Vehicle(ABC):
    # Class variable to track the next available vehicle ID
    _next_vehicle_id = 1
    
    def __init__(self, length, weight, start_node, end_node, image, vehicle_type, energy_type, maximum_speed,
                 liters_per_100km, acceleration=0):
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
        self.cur_road_lane_length = 0
        self.roads_passed = 0
        self.cur_point = self.start_point
        self.vehicle_type = vehicle_type
        self.energy_type = energy_type
        self.maximum_speed = maximum_speed
        self.liters_per_100km = liters_per_100km
        # self.velocity = min(self.cur_road_lane.maximum_speed, self.maximum_speed)
        self.velocity = None
        self.acceleration = acceleration
        self.has_reached_destination = False  # Add flag for destination arrival

        if isinstance(image, str):
            self.image = pygame.image.load(image).convert_alpha()
        else:
            self.image = image

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

    def is_next_lane_the_final_lane(self):
        return self.__end_in_lane is self.lanes_path[self.__lanes_passed]

    def set_start_and_end_nodes(self, start, end):
        self.start_node = start
        self.start_point = start.point
        self.end_node = end
        self.end_point = end.point

    def set_path(self, graph):
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

        self.__end_in_lane = end_in_lane
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

        cur_road_lanes = []
        for lane1, lane2 in self.roads_path:
            if LaneFacing.IN == lane1.facing and LaneFacing.OUT == lane2.facing:
                in_lane = lane1
                out_lane = lane2
            elif LaneFacing.OUT == lane1.facing and LaneFacing.IN == lane2.facing:
                in_lane = lane2
                out_lane = lane1
            else:
                raise TypeError("set_path method is invalid: Invalid order in path: Lane with facing equals to None")
            cur_road_lanes.append(graph.find_road_lanes_by_lanes(out_lane=out_lane, in_lane=in_lane))

        if not cur_road_lanes:
            print("Warning: No road lanes found for path")
            return

        self.cur_road_lane = cur_road_lanes[0][0]
        self.__last_lane = self.lanes_path[self.__lanes_passed]
        print(f"set_path path len: {len(self.lanes_path)}")
        self.__lanes_passed += 1
        print(f"[DEBUG] SET PATH After increment __lanes_passed={self.__lanes_passed}")

    def get_cur_lane(self):
        return self.__last_lane

    def get_next_lane(self):
        if self.__lanes_passed >= len(self.lanes_path):
            return None
        return self.lanes_path[self.__lanes_passed]

    def get_source_junction(self):
        return self.from_junction

    def get_destination_junction(self):
        if self.__lanes_passed > len(self.lanes_path) + 1:
            return None
        return self.to_junction

    def __is_passed_junction(self):
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
            passed = progress > 0.95
            # print(f"[__is_passed_junction] passed={passed} (progress > 0.95: {progress > 0.95})")

        if passed:
            print(
                f"[__is_passed_junction] passed={passed}, setting __last_distance_to_next_junction={current_distance}")
        return passed

    def adapt_out_lanes_to_in_lanes(self):
        # TODO: complete function
        pass

    def setup_move(self):
        # print(f"[setup_move] Starting with __lanes_passed={self.__lanes_passed}, last_lane={self.__last_lane}")
        if self.creation_time is None:
            self.creation_time = time.time()

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

    def cross_junction(self, from_stop: bool):
        try:
            log_vehicle_event(f"[cross_junction] Vehicle #{self.vehicle_id} | from_stop={from_stop} | __lanes_passed={self.__lanes_passed} | __last_lane={self.__last_lane} | queue={getattr(self.__last_lane, 'vehicles_queue', None)}")
            if from_stop:
                vehicle, time_to_sleep = self.__last_lane.pop_head_from_queue()
                log_vehicle_event(f"[cross_junction] Vehicle #{self.vehicle_id} popped from queue, sleeping {time_to_sleep:.2f}s")
                time.sleep(time_to_sleep)
                self.__last_lane.free_to_leave_queue = True
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

            self.__last_lane = self.lanes_path[self.__lanes_passed]
            self.__lanes_passed += 1
            self.__last_lane.road_lane.vehicle_enter_lane(self)
            log_vehicle_event(f"[cross_junction] Vehicle #{self.vehicle_id} entered new lane: {self.__last_lane}")

            if from_stop:
                to_velocity = min(self.__last_lane.road_lane.parent_road.maximum_speed, self.maximum_speed)
                self.total_energy_consumed += self.get_energy_consumption_to_velocity(to_velocity)
                self.total_pollution += self.get_pollution_to_velocity(to_velocity)
                log_vehicle_event(f"[cross_junction] Vehicle #{self.vehicle_id} updated energy={self.total_energy_consumed}, pollution={self.total_pollution}")
        except Exception as e:
            log_vehicle_event(f"[cross_junction][EXCEPTION] Vehicle #{self.vehicle_id}: {e}")

    def move(self, dt):
        dt = dt / 3_600.0
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
                at_front = (self.__last_lane.vehicles_queue != [] and self is self.__last_lane.vehicles_queue[0])
                lane_green = self.__last_lane.cur_state in [State.GREEN, State.GREEN_FLICKERING]
                free_to_leave = self.__last_lane.free_to_leave_queue
                log_vehicle_event(f"[move] Vehicle #{self.vehicle_id} IN-lane: at_front={at_front}, lane_green={lane_green}, free_to_leave={free_to_leave}")
                if lane_green and self.__last_lane.vehicles_queue != [] and free_to_leave:
                    if at_front:
                        log_vehicle_event(f"[move] Vehicle #{self.vehicle_id} is at the front of the queue, lane is green, free_to_leave_queue={free_to_leave}. Starting cross_junction thread.")
                        self.__last_lane.free_to_leave_queue = False
                        try:
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
                    self.roads_passed += 1
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
            nxt = self.lanes_path[self.__lanes_passed].parent_junction.point
            last_junction_point = self.__last_lane.parent_junction.point
            if last_junction_point.get_distance_from_point(nxt) != 0:
                dist = self.cur_point.get_distance_from_point(nxt) * self.cur_road_lane_length / last_junction_point.get_distance_from_point(nxt)
                self.__last_distance_to_next_junction = dist  # in km
        except Exception as e:
            log_vehicle_event(f"[move][EXCEPTION] Vehicle #{self.vehicle_id} in distance calc: {e}")
            raise
        self.velocity += self.acceleration * dt

    # print(f"[move] end of move: velocity now={self.velocity}")
    # if self.__last_distance_to_next_junction is None and self.__next_junction_point:
    #     self.__last_distance_to_next_junction = self.cur_point.get_distance_from_point(self.__next_junction_point)
    #
    # if self.__is_passed_junction() or self.cur_point.get_distance_from_point(self.__next_junction_point) < 5:
    #     if self.nodes_path_index < len(self.nodes_path) - 1:
    #         self.nodes_path_index += 1
    #         self.__next_junction_point = self.nodes_path[self.nodes_path_index].point
    #         self.__last_distance_to_next_junction = self.cur_point.get_distance_from_point(
    #             self.__next_junction_point)
    #     else:
    #         # print(f"[Vehicle] Reached final junction.")
    #         return

    # print(f"[move] Vehicle new position: {self.cur_point.x:.2f}, {self.cur_point.y:.2f}")

    def is_away_from_next_junction_by_less_than_3_seconds(self):
        if LaneFacing.IN == self.__last_lane.facing:
            return False
        time = (self.__last_distance_to_next_junction / self.velocity)
        return 3 > time

    def is_away_from_next_junction_by_between_3_and_7_seconds(self):
        if LaneFacing.IN == self.__last_lane.facing:
            return False
        time = (self.__last_distance_to_next_junction / self.velocity)
        return 7 >= time >= 3

    def is_away_from_next_junction_by_between_7_and_10_seconds(self):
        if LaneFacing.IN == self.__last_lane.facing:
            return False
        time = (self.__last_distance_to_next_junction / self.velocity)
        return 10 > time > 7

    def get_energy_consumption_to_velocity(self, to_velocity):  # returns the kinetic energy in Joule
        return 0.5 * self.weight * (to_velocity ** 2)

    def get_pollution_to_velocity(self, to_velocity):  # CO2 in grams
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
        fuel_in_liters = self.get_energy_consumption_to_velocity(to_velocity) / (0.25 * energy_densities[self.energy_type])
        return emission_factors[self.energy_type] * fuel_in_liters

    def __str__(self):
        return f"(x, y) = {self.get_cur_point().get_point()}"

    def get_cur_point(self):
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

    """
    def get_energy_consumption(self, distance_in_km):
        return self.liters_per_100km * distance_in_km / 100.0

    def get_pollution_emissions(self, distance_in_km):  # CO2 in grams
        return distance_in_km * 2,310  # gasoline prefix (CO2 grams / Liter)
    """

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
        """Track when vehicle stops due to traffic lights/queues"""
        if not self.is_stopped:
            self.is_stopped = True
            self.last_stop_time = time.time()
            self.stops_count += 1
            print(f"[Vehicle #{self.vehicle_id}] Stopped - Total stops: {self.stops_count}")

    def track_movement(self):
        """Track when vehicle starts moving again"""
        if self.is_stopped:
            self.is_stopped = False
            if self.last_stop_time:
                self.idle_time += time.time() - self.last_stop_time
                print(f"[Vehicle #{self.vehicle_id}] Resumed movement - Idle time: {self.idle_time:.2f}s")

    def track_acceleration(self, current_acceleration):
        """Track acceleration events"""
        if current_acceleration > 0 and self.last_velocity <= 0:
            self.acceleration_events += 1
            print(f"[Vehicle #{self.vehicle_id}] Acceleration event - Total: {self.acceleration_events}")
        self.last_velocity = current_acceleration

    def update_total_time(self):
        """Update total time from creation to current time"""
        self.total_time = time.time() - self.creation_time

    def calculate_energy_consumption(self, distance_km,
                                C_rr=0.01,
                                C_d=0.3,
                                A=2.2,
                                air_density=1.225,
                                g=9.81):
        """
        calculates the energy consumption in Joule for driving distance_km kilometers in the same velocity

        param: distance_km: distance in kilometers
        return: Energy in Joule
        """
        distance_m = distance_km * 1000  # distance in meters

        # Rolling Resistance
        F_rr = C_rr * self.weight * g

        # Drag or Air Resistance
        F_drag = 0.5 * air_density * C_d * A * self.velocity ** 2

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

    """
    def calculate_energy_consumption(self, distance_traveled):
        # Calculate energy consumption based on vehicle weight, type, distance, and stops
        # Base consumption per meter based on vehicle type and weight
        base_consumption = {
            "Car": 0.0001,  # kWh per meter per kg
            "Bus": 0.00015,
            "Truck": 0.0002
        }
        
        # Energy type multipliers
        energy_multipliers = {
            "Electric": 1.0,    # Most efficient
            "Gas": 1.2,         # 20% less efficient than electric
            "Gasoline": 1.4     # 40% less efficient than electric
        }
        
        # Stop penalty (extra energy for each stop)
        stop_penalty = self.stops_count * 0.01  # kWh per stop
        
        # Calculate base consumption
        base_energy = base_consumption.get(self.vehicle_type, 0.0001) * self.weight * distance_traveled
        
        # Apply energy type multiplier
        energy_multiplier = energy_multipliers.get(self.energy_type, 1.0)
        total_energy = (base_energy * energy_multiplier) + stop_penalty
        
        return total_energy

    def calculate_pollution(self, distance_traveled):
        # Calculate pollution based on energy type, distance, and vehicle type
        # CO2 emissions per kWh/L based on energy type
        emissions_per_unit = {
            "Electric": 0.5,    # g CO2 per kWh (assuming grid mix)
            "Gas": 2.3,         # g CO2 per L
            "Gasoline": 2.4     # g CO2 per L
        }
        
        # Vehicle type multipliers (heavier vehicles pollute more)
        vehicle_multipliers = {
            "Car": 1.0,
            "Bus": 1.5,
            "Truck": 2.0
        }
        
        # Calculate energy consumption first
        energy_consumed = self.calculate_energy_consumption(distance_traveled)
        
        # Convert to appropriate units for pollution calculation
        if self.energy_type == "Electric":
            # For electric, use kWh directly
            pollution = energy_consumed * emissions_per_unit["Electric"]
        else:
            # For gas/gasoline, convert energy to liters (approximate)
            # Assuming 10 kWh per liter for fossil fuels
            liters_consumed = energy_consumed / 10
            pollution = liters_consumed * emissions_per_unit[self.energy_type]
        
        # Apply vehicle type multiplier
        vehicle_multiplier = vehicle_multipliers.get(self.vehicle_type, 1.0)
        total_pollution = pollution * vehicle_multiplier
        
        return total_pollution
    """

    def calculate_pollution_in_acceleration(self):
        # TODO: complete the func
        pass

    @staticmethod
    def print_vehicles_on_map(vehicles):
        print("\n[VEHICLES ON MAP]")
        for v in vehicles:
            if not v.has_arrived():
                print(f"Vehicle #{v.vehicle_id}: type={v.vehicle_type}, energy={v.energy_type}, cur_point={v.get_cur_point().get_point() if v.get_cur_point() else None}, lane={v.get_cur_lane()}, queue_pos={v.get_queue_position()}")
        print("[END VEHICLES ON MAP]\n")
