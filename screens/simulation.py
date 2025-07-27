import json
import math
import random
import threading

import networkx as nx
import pygame
import sys
import tkinter as tk
from enum import Enum
import time
import os
import copy

from classes.Edges.Road import Road
from classes.Entities.Algorithm import Algorithm
from classes.Entities.Graph import Graph, find_out_lane_by_index_in_junction
from classes.Entities.Point import Point
from classes.Entities.Vehicles.Vehicle import Vehicle
from classes.Enums.Color import Color
from classes.Enums.EdgeDensity import EdgeDensity
from classes.Enums.LaneFacing import LaneFacing
from classes.Nodes.Direction import Direction
from classes.Nodes.Junction import Junction
from classes.Nodes.Lane import Lane
from classes.Enums.State import State


def get_map_from_settings():
    """Get the map name from settings.json."""
    try:
        with open("settings.json", "r") as f:
            settings = json.load(f)
            map_name = settings.get("Map for simulation", {}).get("value", "")
            # Handle case where map_name might be a tuple or list
            if isinstance(map_name, (tuple, list)):
                map_name = map_name[0]
            return map_name
    except Exception:
        return "map1"  # Default to map1 if there's an error


def is_cursor_in_circle(center_point, radius):
    mouse_pos = pygame.mouse.get_pos()
    dx = mouse_pos[0] - center_point.x
    dy = mouse_pos[1] - center_point.y
    return (dx ** 2 + dy ** 2) <= radius ** 2


def collect_consumption_statistics(graph):
    """
    Collect consumption and pollution statistics from all vehicles in the given graph
    """
    total_energy_consumed = 0
    total_pollution = 0
    total_distance = 0
    total_stops = 0
    total_acceleration_events = 0
    total_idle_time = 0

    # Energy type breakdown
    energy_consumption_by_energy_type = {"Electric": 0, "Gasoline": 0, "Gas": 0}
    vehicles_pollution_by_energy_type = {"Electric": 0, "Gasoline": 0, "Gas": 0}

    # Vehicle type breakdown
    energy_consumption_by_vehicle_type = {"Car": 0, "Bus": 0, "Truck": 0}
    vehicles_pollution_by_vehicle_type = {"Car": 0, "Bus": 0, "Truck": 0}

    for vehicle in graph.vehicles:
        # Get consumption summary for this vehicle
        summary = vehicle.get_consumption_summary()

        # Add to totals
        total_energy_consumed += summary["total_energy_consumed"]
        total_pollution += summary["total_pollution"]
        total_distance += summary["total_distance"]
        total_stops += summary["stops_count"]
        total_acceleration_events += summary["acceleration_events"]
        total_idle_time += summary["idle_time"]

        # Add to energy type breakdown
        energy_consumption_by_energy_type[vehicle.energy_type] += summary["total_energy_consumed"]
        vehicles_pollution_by_energy_type[vehicle.energy_type] += summary["total_pollution"]

        # Add to vehicle type breakdown
        energy_consumption_by_vehicle_type[vehicle.vehicle_type] += summary["total_energy_consumed"]
        vehicles_pollution_by_vehicle_type[vehicle.vehicle_type] += summary["total_pollution"]

    return {
        "total_energy_consumed": total_energy_consumed,
        "total_pollution": total_pollution,
        "total_distance": total_distance,
        "total_stops": total_stops,
        "total_acceleration_events": total_acceleration_events,
        "total_idle_time": total_idle_time,
        "energy_consumption": energy_consumption_by_energy_type,
        "energy_pollution": vehicles_pollution_by_energy_type,
        "vehicle_consumption": energy_consumption_by_vehicle_type,
        "vehicle_pollution": vehicles_pollution_by_vehicle_type,
        "average_energy_efficiency": total_energy_consumed / total_distance if total_distance > 0 else 0,
        "average_pollution_efficiency": total_pollution / total_distance if total_distance > 0 else 0
    }


def draw_arrow(surface, color, start, end, width=2, head_size=5):
    # Draw the shaft
    pygame.draw.line(surface, color, start, end, width)

    # Calculate direction of the arrow
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    angle = math.atan2(dy, dx)

    # Compute coordinates for arrowhead
    x, y = end
    left = (x - head_size * math.cos(angle - math.pi / 6),
            y - head_size * math.sin(angle - math.pi / 6))
    right = (x - head_size * math.cos(angle + math.pi / 6),
             y - head_size * math.sin(angle + math.pi / 6))

    # Draw the arrowhead as a filled triangle
    pygame.draw.polygon(surface, color, [end, left, right])


class SimulationScreen:
    def __init__(self, screen, ui_manager, display_alg, compare_alg):
        self.compare_stats = None
        self.display_stats = None
        self._printed_vehicles_on_map = None
        self.screen = screen
        self.ui_manager = ui_manager
        self.display_alg = display_alg
        self.compare_alg = compare_alg
        self.algorithm = None
        self.algorithm_thread = None

        self.stop_event = threading.Event()  # Flag to tell the thread to stop

        self.algorithm_to_compare = None
        self.algorithm_to_compare_thread = None
        self.graph_for_algorithm_to_compare = None

        self.next_screen = None
        self.graph = None
        self.current_junction = None
        self.running = True
        self.is_stopped = False
        self.clock = pygame.time.Clock()
        self.dt = 0
        self.simulation_time = 0  # Add simulation time tracking
        self.main_simulation_time = 0  # Track main sim duration
        self.compare_simulation_time = 0  # Track compare sim duration
        self.all_vehicles_arrived = False  # Add flag for vehicle arrival
        self.all_vehicles_arrived_main = False  # Track main sim
        self.all_vehicles_arrived_compare = False  # Track compare sim
        self.show_loading_screen = False
        self.loading_angle = 0  # For spinner animation
        self.loading_screen_started = False

        root = tk.Tk()
        root.withdraw()
        if None is not self.screen:
            self.WINDOW_WIDTH, self.WINDOW_HEIGHT = self.screen.get_size()
            self.MAIN_WIDTH = (2 * self.WINDOW_WIDTH) // 3
            self.MAIN_HEIGHT = (9 * self.WINDOW_HEIGHT) // 10
            self.SIDE_WIDTH = self.WINDOW_WIDTH - self.MAIN_WIDTH
            self.SIDE_HEIGHT = self.WINDOW_HEIGHT // 2
            self.CONTROL_BAR_HEIGHT = self.WINDOW_HEIGHT - self.MAIN_HEIGHT
            self.DIVIDER_WIDTH = 2
            self.BUTTON_CENTER = Point((self.MAIN_WIDTH // 2), self.MAIN_HEIGHT + (self.CONTROL_BAR_HEIGHT // 2))
            self.BUTTON_RADIUS = 25
            self.FPS = 60

            self.SIMULATION_SCREEN = pygame.Rect(0, 0, self.MAIN_WIDTH, self.MAIN_HEIGHT)
            self.CONTROL_BAR_SCREEN = pygame.Rect(0, self.MAIN_HEIGHT, self.MAIN_WIDTH, self.CONTROL_BAR_HEIGHT)
            self.JUNCTION_SCREEN = pygame.Rect(self.MAIN_WIDTH, 0, self.SIDE_WIDTH, self.SIDE_HEIGHT)
            self.VEHICLE_SCREEN = pygame.Rect(self.MAIN_WIDTH, self.SIDE_HEIGHT, self.SIDE_WIDTH, self.SIDE_HEIGHT)

        self.EDGES_DENSITY = random.choice((EdgeDensity.LOW, EdgeDensity.MEDIUM, EdgeDensity.HIGH))
        self.NUM_NODES = 25
        self.NUM_CARS = 20

        self.vehicle_stats = {
            "Electric": 0,
            "Gasoline": 0,
            "Gas": 0,
            "Private car amount": 0,
            "Buses amount": 0,
            "Trucks amount": 0
        }
        self.load_vehicle_data_from_json()

        # Get map name from settings and load the corresponding map file
        map_name = get_map_from_settings()
        map_path = os.path.join("maps", f"{map_name}.json")
        json_data = json.load(open(map_path, "r"))
        self.set_graph(json_data, 0.01)

    def get_next_screen(self):
        return self.next_screen

    def handle_events(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if is_cursor_in_circle(self.BUTTON_CENTER, self.BUTTON_RADIUS):
                self.is_stopped = not self.is_stopped
            else:
                for junction in self.graph.nodes:
                    if is_cursor_in_circle(junction.point, 6):
                        self.current_junction = junction
                        return

                for vehicle in self.graph.vehicles:
                    if vehicle.cur_point:
                        x, y = int(vehicle.cur_point.x), int(vehicle.cur_point.y)
                        # Draw vehicle as a red dot
                        pygame.draw.circle(
                            self.screen,
                            Color.RED.value,  # ✅ get the actual RGB tuple
                            (x, y),
                            5
                        )

    def update(self, delta_time):
        self.dt = delta_time
        if not self.is_stopped:
            # Update simulation time for both algorithms
            if not self.algorithm.terminate_flag:
                self.main_simulation_time += delta_time
            if not self.algorithm_to_compare.terminate_flag:
                self.compare_simulation_time += delta_time
            # --- Main simulation ---
            all_arrived_main = True
            arrived_count_main = 0
            total_count_main = len(self.graph.vehicles)
            if not self.algorithm.terminate_flag:
                # Move all vehicles in main simulation
                for vehicle in self.graph.vehicles:
                    vehicle.move(delta_time)
                    if not vehicle.has_arrived():
                        all_arrived_main = False
                    else:
                        arrived_count_main += 1

            # --- Compare simulation ---
            all_arrived_compare = True
            arrived_count_compare = 0
            if not self.algorithm_to_compare.terminate_flag:
                # Move all vehicles in comparison simulation
                for vehicle in self.graph_for_algorithm_to_compare.vehicles:
                    vehicle.move(delta_time)
                    if not vehicle.has_arrived():
                        all_arrived_compare = False
                    else:
                        arrived_count_compare += 1

            # Print vehicles on map after 50% have arrived (main sim)
            if not hasattr(self, '_printed_vehicles_on_map'):
                self._printed_vehicles_on_map = False
            if not self._printed_vehicles_on_map and arrived_count_main >= total_count_main // 2:
                Vehicle.print_vehicles_on_map(self.graph.vehicles)
                self._printed_vehicles_on_map = True

            # --- Stop main algorithm if done ---
            if all_arrived_main and not self.algorithm.terminate_flag:
                self.algorithm.terminate_flag = True
                self.algorithm_thread.join()
                self.all_vehicles_arrived_main = True
                # Start loading screen thread if not already started
                if not self.loading_screen_started:
                    self.loading_screen_started = True
                    self.show_loading_screen = True

            # --- Stop compare algorithm if done ---
            if all_arrived_compare and not self.algorithm_to_compare.terminate_flag:
                self.algorithm_to_compare.terminate_flag = True
                self.algorithm_to_compare_thread.join()
                self.all_vehicles_arrived_compare = True

            # --- When both are done, show statistics ---
            if (
                self.all_vehicles_arrived_main
                and self.all_vehicles_arrived_compare
                and not self.all_vehicles_arrived
            ):
                self.show_loading_screen = False
                # Collect stats
                self.display_stats = collect_consumption_statistics(self.graph)
                self.compare_stats = collect_consumption_statistics(self.graph_for_algorithm_to_compare)

                # Transition to statistics screen
                from screens.statistics import StatisticsScreen
                self.next_screen = StatisticsScreen(
                    self.screen,
                    self.ui_manager,
                    len(self.graph.vehicles),
                    self.main_simulation_time,
                    self.compare_simulation_time,
                    self.vehicle_stats,
                    self.display_stats,
                    self.compare_stats,
                    self.display_alg.name,
                    self.compare_alg.name
                )
                self.all_vehicles_arrived = True

    def draw(self):
        if self.show_loading_screen:
            self.draw_loading_spinner()
            return

        self.screen.fill(Color.WHITE.value)

        pygame.draw.rect(self.screen, Color.VERY_DARK_GREY.value, self.SIMULATION_SCREEN)
        pygame.draw.rect(self.screen, Color.VERY_DARK_GREY.value, self.CONTROL_BAR_SCREEN)
        pygame.draw.rect(self.screen, Color.VERY_DARK_GREY.value, self.JUNCTION_SCREEN)
        pygame.draw.rect(self.screen, Color.VERY_DARK_GREY.value, self.VEHICLE_SCREEN)

        pygame.draw.line(self.screen, Color.LIGHT_GREY.value, (0, self.MAIN_HEIGHT), (self.MAIN_WIDTH, self.MAIN_HEIGHT), self.DIVIDER_WIDTH)
        pygame.draw.line(self.screen, Color.LIGHT_GREY.value, (self.MAIN_WIDTH, 0), (self.MAIN_WIDTH, self.WINDOW_HEIGHT), self.DIVIDER_WIDTH)
        pygame.draw.line(self.screen, Color.LIGHT_GREY.value, (self.MAIN_WIDTH, self.SIDE_HEIGHT), (self.WINDOW_WIDTH, self.SIDE_HEIGHT), self.DIVIDER_WIDTH)

        current_button_color = Color.DARK_RED if is_cursor_in_circle(self.BUTTON_CENTER, self.BUTTON_RADIUS) else Color.RED
        text_color = Color.GREY if is_cursor_in_circle(self.BUTTON_CENTER, self.BUTTON_RADIUS) else Color.WHITE

        pygame.draw.circle(self.screen, current_button_color.value, (self.BUTTON_CENTER.x, self.BUTTON_CENTER.y), self.BUTTON_RADIUS)
        font = pygame.font.SysFont("Arial", 30)

        button_text = ">" if self.is_stopped else "| |"
        status_font = pygame.font.SysFont("Arial", 20)
        status_text = "Paused" if self.is_stopped else "Running"
        status_surface = status_font.render(status_text, True, Color.GREY.value)
        status_rect = status_surface.get_rect(center=(self.BUTTON_CENTER.x, self.BUTTON_CENTER.y + 40))
        self.screen.blit(status_surface, status_rect)
        text_surface = font.render(button_text, True, text_color.value)
        text_rect = text_surface.get_rect(center=(self.BUTTON_CENTER.x, self.BUTTON_CENTER.y))
        self.screen.blit(text_surface, text_rect)

        self.draw_graph()
        self.draw_junction()
        self.draw_vehicle()

    def draw_graph(self):
        if self.graph is None:
            return
        self.graph.draw(self.screen, self)

    def draw_junction(self):
        if self.current_junction is None:
            return

        center = (self.WINDOW_WIDTH - (self.SIDE_WIDTH // 2), self.SIDE_HEIGHT // 2)
        self.draw_regular_polygon(self.screen, center, 90, self.current_junction, self.current_junction.directions)


    def get_sorted_vehicles_for_junction(self, junction, from_seconds, to_seconds):
        """Get vehicles sorted by arrival time for a specific junction."""
        if not self.graph or not self.graph.vehicles:
            return []
            
        # Find vehicles that are approaching this junction
        junction_vehicles = []
        for vehicle in self.graph.vehicles:
            if hasattr(vehicle, 'cur_road_lane') and vehicle.cur_road_lane and not vehicle.is_next_lane_the_final_lane():
                # Check if vehicle is heading towards this junction
                next_junction = vehicle.get_destination_junction()
                if next_junction and next_junction.junction_index == junction.junction_index:
                    junction_vehicles.append(vehicle)
        
        # Sort vehicles using the same logic as in RoadLane
        try:
            sorted_vehicles = sorted(junction_vehicles, 
                                   key=lambda obj: getattr(obj, "is_away_from_next_junction_by_between_start_and_end_seconds")(from_seconds, to_seconds))
            return sorted_vehicles
        except Exception:
            # Error sorting vehicles for junction
            return junction_vehicles

    def draw_vehicle(self):
        if not self.graph or not self.graph.vehicles:
            return
        
        font = pygame.font.SysFont("Arial", 18)
        x_start = self.MAIN_WIDTH + 20
        y_start = self.SIDE_HEIGHT + 20
        line_height = 30
        column_widths = [60, 60, 70, 70]  # Adjusted widths

        # Table headers
        headers = ["Vehicle", "Gas", "Gasoline", "Electric"]
        for idx, header in enumerate(headers):
            rect = pygame.Rect(x_start + sum(column_widths[:idx]), y_start, column_widths[idx], line_height)
            pygame.draw.rect(self.screen, Color.GREY.value, rect, border_radius=3)
            pygame.draw.rect(self.screen, Color.WHITE.value, rect, 1)
            text = font.render(header, True, Color.WHITE.value)
            self.screen.blit(text, (rect.x + 5, rect.y + 5))

        y = y_start + line_height

        # Count vehicles by type and energy
        stats = {
            "Car": {"Gas": 0, "Gasoline": 0, "Electric": 0},
            "Bus": {"Gas": 0, "Gasoline": 0, "Electric": 0},
            "Truck": {"Gas": 0, "Gasoline": 0, "Electric": 0},
        }

        # Count arrived vehicles (all types)
        total_vehicles = 0
        arrived_vehicles = 0

        for v in self.graph.vehicles:
            v_type = getattr(v, "vehicle_type", "Unknown")
            energy = getattr(v, "energy_type", "Unknown")

            if v_type in stats and energy in stats[v_type]:
                stats[v_type][energy] += 1

            total_vehicles += 1
            if hasattr(v, "has_arrived") and v.has_arrived():
                arrived_vehicles += 1

        for v_type, counts in stats.items():
            row = [v_type, str(counts["Gas"]), str(counts["Gasoline"]), str(counts["Electric"])]
            for idx, value in enumerate(row):
                rect = pygame.Rect(x_start + sum(column_widths[:idx]), y, column_widths[idx], line_height)
                pygame.draw.rect(self.screen, Color.GREY.value, rect)
                pygame.draw.rect(self.screen, Color.WHITE.value, rect, 1)
                text = font.render(value, True, Color.WHITE.value)
                self.screen.blit(text, (rect.x + 5, rect.y + 5))
            y += line_height

        # Draw arrived vehicles counter under the table
        counter_text = f"Arrived: {arrived_vehicles} / {total_vehicles} vehicles"
        counter_font = pygame.font.SysFont("Arial", 18, bold=True)
        counter_surface = counter_font.render(counter_text, True, Color.WHITE.value)
        self.screen.blit(counter_surface, (x_start, y + 10))

    def draw_regular_polygon(self, surface, center, radius, current_junction, directions, width=0, lane_length=100):
        num_sides = current_junction.size
        label_text = f"Junction {current_junction.junction_index}"
        label_surface = pygame.font.SysFont("arial", 20).render(label_text, True, (255, 255, 255))
        text_rect = label_surface.get_rect(center=(center[0], center[1] - radius - 20))
        surface.blit(label_surface, text_rect)

        if num_sides == 2:
           num_sides = 4

        angle_step = 2 * math.pi / num_sides
        points = [(center[0] + radius * math.cos(i * angle_step - math.pi / 2),
                   center[1] + radius * math.sin(i * angle_step - math.pi / 2)) for i in range(num_sides)]

        pygame.draw.polygon(surface, Color.GREY.value, points, width)

        # Find nearby vehicles
        nearby_vehicles = []

        for vehicle in self.graph.vehicles:
            if hasattr(vehicle, 'cur_point'):
                vehicle_x = vehicle.cur_point.x
                vehicle_y = vehicle.cur_point.y

                dx_to_center = vehicle_x - center[0]
                dy_to_center = vehicle_y - center[1]
                distance_to_center = math.sqrt(dx_to_center * dx_to_center + dy_to_center * dy_to_center)

                # Check if vehicle is near this junction - increased threshold to 1000
                if distance_to_center < 1000:  # Increased from 500 to 1000
                    if hasattr(vehicle, 'cur_road_lane') and vehicle.get_source_junction():

                        # Get current junction from source lane
                        current_vehicle_junction = vehicle.get_source_junction()

                        # Get next junction from destination lane
                        next_vehicle_junction = vehicle.get_destination_junction()

                        # Check if vehicle is near this junction
                        is_near_current = current_vehicle_junction and current_vehicle_junction.junction_index == current_junction.junction_index
                        is_near_next = next_vehicle_junction and next_vehicle_junction.junction_index == current_junction.junction_index
                        
                        if is_near_current or is_near_next:
                            nearby_vehicles.append((vehicle, distance_to_center))

        # Draw lanes and vehicles
        for i in range(min(num_sides, len(directions))):  # Ensure we don't exceed the number of directions
            p1, p2 = points[i], points[(i + 1) % num_sides]
            direction = directions[i]

            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            edge_length = math.hypot(dx, dy)
            dir_x, dir_y = dx / edge_length, dy / edge_length
            ortho_x, ortho_y = dir_y, -dir_x  # perpendicular outward

            total_lanes = len(direction.in_lanes) + len(direction.out_lanes)
            lane_step = edge_length / (total_lanes + 1)
            # Draw IN lanes
            for lane_index, lane in enumerate(direction.in_lanes):
                offset = lane_step * (lane_index + 1)
                end_x = p1[0] + dir_x * offset  # End at junction
                end_y = p1[1] + dir_y * offset
                start_x = end_x + ortho_x * lane_length  # Start away from junction
                start_y = end_y + ortho_y * lane_length
                draw_arrow(surface, lane.get_lane_color().value, (start_x, start_y), (end_x, end_y))

                # Draw vehicles on this lane
                for vehicle, distance in nearby_vehicles:
                    if hasattr(vehicle, 'has_arrived') and vehicle.has_arrived():
                        continue  # Skip drawing if vehicle reached destination
                    if hasattr(vehicle, 'cur_road_lane') and vehicle.get_cur_lane():
                        # For IN lanes, check if this is the destination lane
                        if vehicle.get_next_lane() == lane:
                            # Calculate progress based on time
                            if hasattr(vehicle, 'velocity') and vehicle.velocity is not None:
                                # Get source and destination nodes from the current road lane
                                from_node = vehicle.get_source_junction().point
                                to_node = vehicle.get_destination_junction().point

                                # Calculate current distance from start of road
                                current_distance = vehicle.cur_point.get_distance_from_point(from_node)
                                total_distance = from_node.get_distance_from_point(to_node)
                                progress = current_distance / total_distance if total_distance > 0 else 0

                                # Only draw if progress is less than 0.99 or light is green
                                if progress < 0.99 and progress != 0:
                                    lane_x = start_x + (end_x - start_x) * progress
                                    lane_y = start_y + (end_y - start_y) * progress
                                    pygame.draw.circle(surface, Color.RED.value, (int(lane_x), int(lane_y)), 3)
                                elif (progress >= 0.99 or progress == 0) and (
                                        lane.get_lane_color() == Color.YELLOW or lane.get_lane_color() == Color.RED or lane.get_lane_color() == Color.ORANGE):
                                    vehicle.need_to_stop = True
                                    lane_x = start_x + (end_x - start_x) * 0.99
                                    lane_y = start_y + (end_y - start_y) * 0.99
                                    pygame.draw.circle(surface, Color.SKY_BLUE.value, (int(lane_x), int(lane_y)), 3)
                                else:
                                    vehicle.need_to_stop = False
            # Draw OUT lanes
            for lane_index, lane in enumerate(direction.out_lanes):
                offset = lane_step * (lane_index + 1 + len(direction.in_lanes))
                start_x = p1[0] + dir_x * offset  # Start at junction
                start_y = p1[1] + dir_y * offset
                end_x = start_x + ortho_x * lane_length  # End away from junction
                end_y = start_y + ortho_y * lane_length
                draw_arrow(surface, lane.get_lane_color().value, (start_x, start_y), (end_x, end_y))

                # Draw vehicles on this lane
                for vehicle, distance in nearby_vehicles:
                    if hasattr(vehicle, 'has_arrived') and vehicle.has_arrived():
                        continue  # Skip drawing if vehicle reached destination
                    if hasattr(vehicle, 'cur_road_lane') and vehicle.cur_road_lane:
                        # For OUT lanes, check if this is the source lane
                        if vehicle.get_cur_lane() == lane:
                            # Calculate progress based on time
                            if hasattr(vehicle, 'velocity') and vehicle.velocity is not None:
                                
                                # Get source and destination nodes from the current road lane
                                from_node = vehicle.get_source_junction().point
                                to_node = vehicle.get_destination_junction().point
                                
                                # Calculate current distance from start of road
                                current_distance = vehicle.cur_point.get_distance_from_point(from_node)
                                total_distance = from_node.get_distance_from_point(to_node)
                                progress = current_distance / total_distance if total_distance > 0 else 0

                                # Only draw if progress is less than 0.99 or light is green
                                if progress < 0.99:
                                    lane_x = start_x + (end_x - start_x) * progress
                                    lane_y = start_y + (end_y - start_y) * progress
                                    pygame.draw.circle(surface, Color.RED.value, (int(lane_x), int(lane_y)), 3)
                                elif progress >= 0.99 and (lane.get_lane_color() == Color.YELLOW or lane.get_lane_color() == Color.RED or lane.get_lane_color() == Color.ORANGE):
                                    lane_x = start_x + (end_x - start_x) * 0.99
                                    lane_y = start_y + (end_y - start_y) * 0.99
                                    pygame.draw.circle(surface, Color.SKY_BLUE.value, (int(lane_x), int(lane_y)), 3)

    def set_graph(self, json_data, dt):
        directions_in_map = []  # sorted by indexes in map

        # Extract junctions as nodes (focus on out lanes)
        nodes = []
        junctions = json_data.get("Junctions", {})
        junction_index = 0
        for junction_name, junction_data in junctions.items():
            nodes.append(Junction())
            direction_index = 0
            for direction_name, direction_data in junction_data.items():
                direction = Direction(direction_data["Index_in_map"])
                direction.set_parent_junction(nodes[junction_index])
                nodes[junction_index].add_direction(direction)
                directions_in_map.append(direction)
                for out_lane_name, out_lane_index_in_junction in direction_data.get("Out_Lanes", {}).items():
                    out_lane = Lane(LaneFacing.OUT, index_in_junction=out_lane_index_in_junction)
                    out_lane.set_parent_direction(direction)
                    nodes[junction_index].directions[direction_index].add_to_left(out_lane)
                direction_index += 1
            junction_index += 1

        # (focus on in lanes and their to-lanes)
        junction_index = 0
        for junction_name, junction_data in junctions.items():
            direction_index = 0
            for direction_name, direction_data in junction_data.items():
                direction = nodes[junction_index].directions[direction_index]
                for in_lane_name, in_lane_data in direction_data.get("In_Lanes", {}).items():
                    to_lanes = []
                    for to_lane_name, to_lane_index_in_junction in in_lane_data.get("To_Lanes", {}).items():
                        out_lane = find_out_lane_by_index_in_junction(nodes[junction_index], to_lane_index_in_junction)
                        to_lanes.append(out_lane)
                    in_lane = Lane(LaneFacing.IN, to_lanes=to_lanes)
                    in_lane.set_parent_direction(direction)
                    nodes[junction_index].directions[direction_index].add_to_left(in_lane)
                    nodes[junction_index].junction_index = junction_index
                direction_index += 1
            junction_index += 1

        # Extract roads as edges
        edges = []
        roads = json_data.get("Roads", {})
        for road_name, road_data in roads.items():
            first_direction = directions_in_map[road_data["direction1_index_in_map"]]
            second_direction = directions_in_map[road_data["direction2_index_in_map"]]
            length = road_data["length"]  # in meters
            max_speed = road_data["max_speed"]
            road = Road(road_name, first_direction, second_direction, length, max_speed)
            first_direction.set_road(road)
            second_direction.set_road(road)
            edges.append(road)

        # Step 4: Apply Layout
        self.force_directed_layout(nodes, edges)

        # Step 5: Vehicle creation with correct energy type distribution
        vehicles = []
        vehicle_stats = self.vehicle_stats
        total_vehicles = vehicle_stats["Private car amount"] + vehicle_stats["Buses amount"] + vehicle_stats[
            "Trucks amount"]
        energy_types = ["Electric", "Gasoline", "Gas"]
        energy_distribution = []

        # Create energy type distribution based on percentages
        for energy in energy_types:
            count = int((vehicle_stats[energy] / 100) * total_vehicles)
            energy_distribution.extend([energy] * count)

        # In case rounding left out some slots
        while len(energy_distribution) < total_vehicles:
            energy_distribution.append(random.choice(energy_types))

        # Shuffle to randomize energy type assignment
        random.shuffle(energy_distribution)

        vehicle_types = (
            ("Car", vehicle_stats["Private car amount"]),
            ("Bus", vehicle_stats["Buses amount"]),
            ("Truck", vehicle_stats["Trucks amount"])
        )

        # Create vehicles with random source/destination pairs
        for v_type, amount in vehicle_types:
            for _ in range(amount):
                if not energy_distribution:
                    break
                # Randomly select source and destination nodes (must be different)
                src_node = random.choice(nodes)
                dst_node = random.choice([n for n in nodes if n != src_node])
                weight = random.randint(1200, 2400)  # Random vehicle weight
                energy = energy_distribution.pop()
                vehicles.append(Vehicle(
                    length=2,
                    weight=weight,
                    start_node=src_node,
                    end_node=dst_node,
                    vehicle_type=v_type,
                    energy_type=energy,
                    acceleration=0,  # or adjust per type if needed
                    maximum_speed=100
                ))

        # --- Set states --- #

        for junction in nodes:
            junction.set_states()

        self.graph = Graph(nodes, edges, vehicles, dt)

        # --- Set paths --- #

        for vehicle in self.graph.vehicles:
            vehicle.set_path(self.graph)

        # --- Set algorithms --- #

        self.graph_for_algorithm_to_compare = copy.deepcopy(self.graph)

        self.algorithm = Algorithm(self.display_alg, self.graph.nodes)
        self.algorithm_thread = threading.Thread(target=self.algorithm.run)

        self.algorithm_to_compare = Algorithm(self.compare_alg, self.graph_for_algorithm_to_compare.nodes)
        self.algorithm_to_compare_thread = threading.Thread(target=self.algorithm_to_compare.run)

        # Start threads
        self.algorithm_thread.start()
        self.algorithm_to_compare_thread.start()

    def force_directed_layout(self, nodes, edges):
        # Create NetworkX graph for layout calculation
        graph = nx.Graph()
        node_id_map = {node: idx for idx, node in enumerate(nodes)}
        id_node_map = {idx: node for node, idx in node_id_map.items()}
        
        # Add edges to graph (only between different nodes)
        for edge in edges:
            src, dst = edge.first_direction.parent_junction, edge.second_direction.parent_junction
            if src != dst:
                graph.add_edge(node_id_map[src], node_id_map[dst])
        
        # Calculate spring layout positions using NetworkX
        pos = nx.spring_layout(graph, seed=42)
        padding = 50
        area_width = self.SIMULATION_SCREEN.width - 2 * padding
        area_height = self.SIMULATION_SCREEN.height - 2 * padding
        
        # Convert layout coordinates to screen coordinates
        for node_id, (x, y) in pos.items():
            # Map from [-1,1] range to screen coordinates with padding
            id_node_map[node_id].point = Point(int(padding + (x + 1) / 2 * area_width),
                                               int(padding + (y + 1) / 2 * area_height))

    def load_vehicle_data_from_json(self, file_path="settings.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                self.vehicle_stats["Private car amount"] = int(data.get("Private car amount", {}).get("value", 0))
                self.vehicle_stats["Buses amount"] = int(data.get("Buses amount", {}).get("value", 0))
                self.vehicle_stats["Trucks amount"] = int(data.get("Trucks amount", {}).get("value", 0))
                self.vehicle_stats["Electric"] = int(data.get("Electric", {}).get("value", 0))
                self.vehicle_stats["Gasoline"] = int(data.get("Gasoline", {}).get("value", 0))
                self.vehicle_stats["Gas"] = int(data.get("Gas", {}).get("value", 0))
        except Exception:
            # Failed to load vehicle data from JSON
            pass

    def draw_loading_spinner(self):
        rect = self.SIMULATION_SCREEN
        center = (rect.x + rect.width // 2, rect.y + rect.height // 2)
        radius = 30
        num_dots = 12
        angle = self.loading_angle
        speed = 0.15

        pygame.draw.rect(self.screen, Color.LIGHT_GREY.value, rect)
        for i in range(num_dots):
            a = angle + i * (2 * math.pi / num_dots)
            x = int(center[0] + radius * math.cos(a))
            y = int(center[1] + radius * math.sin(a))
            shade = 255 - int((i / num_dots) * 200)
            pygame.draw.circle(self.screen, (shade, shade, shade), (x, y), 5)
        self.loading_angle += speed
        pygame.display.flip()
