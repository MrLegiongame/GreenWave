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
from classes.Entities.Vehicles.Vehicle import Vehicle, get_image_list
from classes.Enums.Alg import Alg, ALGORITHM_SIZE
from classes.Enums.Color import Color
from classes.Entities.Simulation import Simulation
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
    except Exception as e:
        print(f"[ERROR] Failed to read settings.json: {e}")
        return "map1"  # Default to map1 if there's an error


class SimulationScreen:
    def __init__(self, screen, ui_manager, display_alg, compare_alg):
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
        self.all_vehicles_arrived = False  # Add flag for vehicle arrival

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
        print(f"[DEBUG] Loading map from: {map_path}")
        json_data = json.load(open(map_path, "r"))
        self.set_graph(json_data, 0.01)

    def get_next_screen(self):
        return self.next_screen

    def handle_events(self, event):
        if event.type == pygame.QUIT:
            print("[EVENT] Quit event received.")
            self.running = False
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            print(f"[DEBUG] Mouse clicked at {mouse_pos}")
            if self.is_cursor_in_circle(self.BUTTON_CENTER, self.BUTTON_RADIUS):
                print(f"[DEBUG] Pause button clicked. is_stopped was: {self.is_stopped}")
                self.is_stopped = not self.is_stopped
                print(f"[DEBUG] is_stopped is now: {self.is_stopped}")
            else:
                for junction in self.graph.nodes:
                    if self.is_cursor_in_circle(junction.point, 6):
                        self.current_junction = junction
                        print(f"[EVENT] Junction selected at {junction.point}")
                        return
                for vehicle in self.graph.vehicles:
                    if vehicle.cur_point:
                        x, y = int(vehicle.cur_point.x), int(vehicle.cur_point.y)
                        print(f"[DRAW] Vehicle at ({x}, {y})")
                        # Draw vehicle as a red dot
                        pygame.draw.circle(
                            self.screen,
                            Color.RED.value,  # ✅ get the actual RGB tuple
                            (x, y),
                            5
                        )
                    else:
                        print("[DRAW] Vehicle has no cur_point!")
                    # if self.is_cursor_in_circle(vehicle.cur_point, 5):
                    #     self.sim.set_current_vehicle(vehicle)
                    #     print(f"[EVENT] Vehicle selected at {vehicle.cur_point}")
                    #     return

    def loading_screen(self):
        center = (self.WINDOW_WIDTH // 2, self.WINDOW_HEIGHT // 2)
        radius = 30
        num_dots = 12
        angle = 0
        speed = 0.15  # rotation speed

        running = True
        while not self.all_vehicles_arrived and running:

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            rect = pygame.Rect(center[0] - 250, center[1] - 150, center[0] + 250, center[1] + 150)
            pygame.draw.rect(self.screen, Color.LIGHT_GREY.value, rect)
            pygame.display.flip()
            print("background printed")  # TODO: delete later - for test purposes only

            # draw spinner
            for i in range(num_dots):
                a = angle + i * (2 * math.pi / num_dots)
                x = int(center[0] + radius * math.cos(a))
                y = int(center[1] + radius * math.sin(a))
                shade = 255 - int((i / num_dots) * 200)
                pygame.draw.circle(self.screen, (shade, shade, shade), (x, y), 5)
                pygame.display.flip()
                # time.sleep(0.2)  # TODO: delete later - for test purposes only

            print("spinner printed")  # TODO: delete later - for test purposes only
            angle += speed
            pygame.display.flip()

    def is_cursor_in_circle(self, center_point, radius):
        mouse_pos = pygame.mouse.get_pos()
        dx = mouse_pos[0] - center_point.x
        dy = mouse_pos[1] - center_point.y
        return (dx ** 2 + dy ** 2) <= radius ** 2

    def update(self, delta_time):
        #print(f"[DEBUG] update() called. is_stopped = {self.is_stopped}")
        self.dt = delta_time
        if not self.is_stopped:
            # Update simulation time
            self.simulation_time += delta_time
            
            # Check if all vehicles have arrived
            all_arrived = True
            arrived_count = 0
            total_count = len(self.graph.vehicles)
            for vehicle in self.graph.vehicles:
                vehicle.move(delta_time)
                if not vehicle.has_arrived():  # You'll need to implement this method in Vehicle class
                    all_arrived = False
                else:
                    arrived_count += 1

            # Print vehicles on map after 50% have arrived (only once)
            if not hasattr(self, '_printed_vehicles_on_map'):
                self._printed_vehicles_on_map = False
            if not self._printed_vehicles_on_map and arrived_count >= total_count // 2:
                Vehicle.print_vehicles_on_map(self.graph.vehicles)
                self._printed_vehicles_on_map = True

            # Also move vehicles for the compare algorithm
            for vehicle in self.graph_for_algorithm_to_compare.vehicles:
                vehicle.move(delta_time)
            
            if all_arrived and not self.all_vehicles_arrived:
                self.algorithm.terminate_flag = True
                self.algorithm_to_compare.terminate_flag = True

                loading_thread = threading.Thread(target=self.loading_screen)
                print("starting loading thread")  # TODO: delete later - for test purposes only
                loading_thread.start()

                self.stop_event.set()
                self.algorithm_thread.join()
                self.algorithm_to_compare_thread.join()
                self.all_vehicles_arrived = True

                time.sleep(2)  # TODO: delete later - for test purposes only
                print("ending loading thread")  # TODO: delete later - for test purposes only
                loading_thread.join()

                # Collect consumption statistics before transitioning
                self.display_stats = self.collect_consumption_statistics(self.graph)
                self.compare_stats = self.collect_consumption_statistics(self.graph_for_algorithm_to_compare)

                # Transition to statistics screen
                from screens.statistics import StatisticsScreen
                self.next_screen = StatisticsScreen(
                    self.screen,
                    self.ui_manager,
                    len(self.graph.vehicles),
                    self.simulation_time,
                    self.vehicle_stats,  # Pass vehicle statistics
                    self.display_stats,    # Pass display algorithm statistics
                    self.compare_stats     # Pass compare algorithm statistics
                )
        else:
            print("[UPDATE] Simulation paused.")

    def draw(self):

        #print("[DRAW] Redrawing screen...")
        self.screen.fill(Color.WHITE.value)

        pygame.draw.rect(self.screen, Color.VERY_DARK_GREY.value, self.SIMULATION_SCREEN)
        pygame.draw.rect(self.screen, Color.VERY_DARK_GREY.value, self.CONTROL_BAR_SCREEN)
        pygame.draw.rect(self.screen, Color.VERY_DARK_GREY.value, self.JUNCTION_SCREEN)
        pygame.draw.rect(self.screen, Color.VERY_DARK_GREY.value, self.VEHICLE_SCREEN)

        pygame.draw.line(self.screen, Color.LIGHT_GREY.value, (0, self.MAIN_HEIGHT), (self.MAIN_WIDTH, self.MAIN_HEIGHT), self.DIVIDER_WIDTH)
        pygame.draw.line(self.screen, Color.LIGHT_GREY.value, (self.MAIN_WIDTH, 0), (self.MAIN_WIDTH, self.WINDOW_HEIGHT), self.DIVIDER_WIDTH)
        pygame.draw.line(self.screen, Color.LIGHT_GREY.value, (self.MAIN_WIDTH, self.SIDE_HEIGHT), (self.WINDOW_WIDTH, self.SIDE_HEIGHT), self.DIVIDER_WIDTH)

        current_button_color = Color.DARK_RED if self.is_cursor_in_circle(self.BUTTON_CENTER, self.BUTTON_RADIUS) else Color.RED
        text_color = Color.GREY if self.is_cursor_in_circle(self.BUTTON_CENTER, self.BUTTON_RADIUS) else Color.WHITE

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
        num_sides = self.current_junction.size
        #lanes_per_direction = [len(direction.in_lanes) + len(direction.out_lanes) for direction in self.current_junction.directions]
        #print("Lanes per direction:" , lanes_per_direction)
        self.draw_regular_polygon(self.screen, center, 90, self.current_junction, self.current_junction.directions)

    def draw_vehicle(self):
        if not self.graph or not self.graph.vehicles:
            print("[DRAW] No vehicle data to display.")
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
            else:
                print(f"[WARNING] Unexpected vehicle type or energy: {v_type}, {energy}")

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

    def draw_arrow(self, surface, color, start, end, width=2, head_size=5):
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

    def draw_regular_polygon(self, surface, center, radius, current_junction, directions, width=0, lane_spacing=10,
                             lane_length=100):
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
        #print(f"\n[DEBUG] Checking vehicles for junction {current_junction.junction_index}")
        #print(f"[DEBUG] Junction center: ({center[0]}, {center[1]})")
        #print(f"[DEBUG] Total vehicles in graph: {len(self.graph.vehicles)}")

        for vehicle in self.graph.vehicles:
            #print(f"\n[DEBUG] Checking vehicle {id(vehicle)}")
            if hasattr(vehicle, 'cur_point'):
                vehicle_x = vehicle.cur_point.x
                vehicle_y = vehicle.cur_point.y
                #print(f"[DEBUG] Vehicle position: ({vehicle_x}, {vehicle_y})")

                dx_to_center = vehicle_x - center[0]
                dy_to_center = vehicle_y - center[1]
                distance_to_center = math.sqrt(dx_to_center * dx_to_center + dy_to_center * dy_to_center)
                #print(f"[DEBUG] Distance to center: {distance_to_center}")

                # Check if vehicle is near this junction - increased threshold to 1000
                if distance_to_center < 1000:  # Increased from 500 to 1000
                    #print("[DEBUG] Vehicle is within range")
                    if hasattr(vehicle, 'cur_road_lane') and vehicle.get_source_junction():
                        #print(f"[DEBUG] Vehicle has road lane: {vehicle.cur_road_lane}")
                        # Get the junction this vehicle is currently in
                        current_vehicle_junction = None
                        next_vehicle_junction = None

                        # Get current junction from source lane
                        current_vehicle_junction = vehicle.get_source_junction()
                        #print(f"[DEBUG] Vehicle source lane junction: {current_vehicle_junction.junction_index if current_vehicle_junction else 'None'}")

                        # Get next junction from destination lane
                        next_vehicle_junction = vehicle.get_destination_junction()
                        #print(f"[DEBUG] Vehicle destination lane junction: {next_vehicle_junction.junction_index if next_vehicle_junction else 'None'}")

                        
                        #print(f"[DEBUG] Vehicle junctions: {current_vehicle_junction.junction_index}, {next_vehicle_junction.junction_index if next_vehicle_junction else 'None'}")
                        #print(f"[DEBUG] Current junction being drawn: {current_junction.junction_index}")
                        
                        # Check if vehicle is near this junction
                        is_near_current = current_vehicle_junction and current_vehicle_junction.junction_index == current_junction.junction_index
                        is_near_next = next_vehicle_junction and next_vehicle_junction.junction_index == current_junction.junction_index
                       # print(f"[DEBUG] Is near current junction: {is_near_current}, Is near next junction: {is_near_next}")
                        
                        if is_near_current or is_near_next:
                            nearby_vehicles.append((vehicle, distance_to_center))
                            # print(f"[DEBUG] Added vehicle to nearby_vehicles list")
                    else:
                        print("[DEBUG] Vehicle has no road lane")
                else:
                    print("[DEBUG] Vehicle is too far from junction")
            else:
                print("[DEBUG] Vehicle has no cur_point")

        # print(f"\n[DEBUG] Found {len(nearby_vehicles)} nearby vehicles")

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
                self.draw_arrow(surface, lane.get_lane_color().value, (start_x, start_y), (end_x, end_y))

                # Draw vehicles on this lane
                for vehicle, distance in nearby_vehicles:
                    if hasattr(vehicle, 'has_arrived') and vehicle.has_arrived():
                        continue  # Skip drawing if vehicle reached destination
                    if hasattr(vehicle, 'cur_road_lane') and vehicle.get_cur_lane():
                        # For IN lanes, check if this is the destination lane
                        # print(f"[DEBUG] Checked lane: {lane} for vehicle: {vehicle.get_cur_lane()}")
                        if vehicle.get_next_lane() == lane:
                            # Calculate progress based on time
                            if hasattr(vehicle, 'velocity') and vehicle.velocity is not None:
                                # Get the road properties
                                # road = vehicle.get_cur_lane().parent_road

                                # Get source and destination nodes from the current road lane
                                from_node = vehicle.get_source_junction().point
                                to_node = vehicle.get_destination_junction().point
                                # road_length = road.length
                                pixel_length = from_node.get_distance_from_point(to_node)

                                # Calculate current distance from start of road
                                current_distance = vehicle.cur_point.get_distance_from_point(from_node)
                                total_distance = from_node.get_distance_from_point(to_node)
                                progress = current_distance / total_distance if total_distance > 0 else 0

                                # Check traffic light state for this lane
                                light_state = getattr(lane, 'cur_state', None)
                                should_wait = light_state not in [State.GREEN, State.GREEN_FLICKERING]

                                # Only draw if progress is less than 0.95 or light is green
                                if progress < 0.95 and progress != 0:
                                    lane_x = start_x + (end_x - start_x) * progress
                                    lane_y = start_y + (end_y - start_y) * progress
                                    pygame.draw.circle(surface, Color.RED.value, (int(lane_x), int(lane_y)), 3)
                                elif (progress >= 0.95 or progress == 0) and (
                                        lane.get_lane_color() == Color.YELLOW or lane.get_lane_color() == Color.RED or lane.get_lane_color() == Color.ORANGE):
                                    print(f"[DEBUG] Progress is {progress} with color {lane.get_lane_color()}")
                                    vehicle.need_to_stop = True
                                    lane_x = start_x + (end_x - start_x) * 0.95
                                    lane_y = start_y + (end_y - start_y) * 0.95
                                    pygame.draw.circle(surface, Color.SKY_BLUE.value, (int(lane_x), int(lane_y)), 3)
                                else:
                                    print(f"[DEBUG] need_to_stop Flase with color {lane.get_lane_color()}")
                                    vehicle.need_to_stop = False
            # Draw OUT lanes
            for lane_index, lane in enumerate(direction.out_lanes):
                offset = lane_step * (lane_index + 1 + len(direction.in_lanes))
                start_x = p1[0] + dir_x * offset  # Start at junction
                start_y = p1[1] + dir_y * offset
                end_x = start_x + ortho_x * lane_length  # End away from junction
                end_y = start_y + ortho_y * lane_length
                self.draw_arrow(surface, lane.get_lane_color().value, (start_x, start_y), (end_x, end_y))

                # Draw vehicles on this lane
                for vehicle, distance in nearby_vehicles:
                    if hasattr(vehicle, 'has_arrived') and vehicle.has_arrived():
                        continue  # Skip drawing if vehicle reached destination
                    if hasattr(vehicle, 'cur_road_lane') and vehicle.cur_road_lane:
                        # For OUT lanes, check if this is the source lane
                        if vehicle.get_cur_lane() == lane:
                            # Calculate progress based on time
                            if hasattr(vehicle, 'velocity') and vehicle.velocity is not None:
                                # Get the road properties
                                #road = vehicle.get_cur_lane().parent_road
                                
                                # Get source and destination nodes from the current road lane
                                from_node = vehicle.get_source_junction().point
                                to_node = vehicle.get_destination_junction().point
                                #road_length = road.length
                                pixel_length = from_node.get_distance_from_point(to_node)
                                
                                # Calculate current distance from start of road
                                current_distance = vehicle.cur_point.get_distance_from_point(from_node)
                                total_distance = from_node.get_distance_from_point(to_node)
                                progress = current_distance / total_distance if total_distance > 0 else 0

                                # Only draw if progress is less than 0.95 or light is green
                                if progress < 0.95:
                                    lane_x = start_x + (end_x - start_x) * progress
                                    lane_y = start_y + (end_y - start_y) * progress
                                    pygame.draw.circle(surface, Color.RED.value, (int(lane_x), int(lane_y)), 3)
                                elif progress >= 0.95 and (lane.get_lane_color() == Color.YELLOW or lane.get_lane_color() == Color.RED or lane.get_lane_color() == Color.ORANGE):
                                    print(f"[DEBUG] Progress is {progress} with color {lane.get_lane_color()}")
                                    lane_x = start_x + (end_x - start_x) * 0.95
                                    lane_y = start_y + (end_y - start_y) * 0.95
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

        for energy in energy_types:
            count = int((vehicle_stats[energy] / 100) * total_vehicles)
            energy_distribution.extend([energy] * count)

        # In case rounding left out some slots
        while len(energy_distribution) < total_vehicles:
            energy_distribution.append(random.choice(energy_types))

        random.shuffle(energy_distribution)

        vehicle_types = (
            ("Car", vehicle_stats["Private car amount"]),
            ("Bus", vehicle_stats["Buses amount"]),
            ("Truck", vehicle_stats["Trucks amount"])
        )

        for v_type, amount in vehicle_types:
            for _ in range(amount):
                if not energy_distribution:
                    break
                src_node = random.choice(nodes)
                dst_node = random.choice([n for n in nodes if n != src_node])
                weight = random.randint(1200, 2400)
                energy = energy_distribution.pop()
                image = random.choice(get_image_list("assets/vehicles/cars"))
                vehicles.append(Vehicle(
                    length=2,
                    weight=weight,
                    start_node=src_node,
                    end_node=dst_node,
                    image=image,
                    vehicle_type=v_type,
                    energy_type=energy,
                    acceleration=0,  # or adjust per type if needed
                    maximum_speed=100,
                    liters_per_100km=random.randint(5, 15)
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

    """
    def set_random_graph(self):
        class Direction_Matrix_Row:
            def __init__(self, junction, size):
                self.junction = junction
                self.row = [0] * size
                self.size = size
                self.directions_amount = 0

            def fill_row(self):
                pass

        self.NUM_CARS

        nodes = []
        edges = []
        vehicles = []
        direction_matrix = []

        # set junctions and direction_matrix
        for index in range(self.NUM_NODES):
            nodes.append(Junction())
            direction_matrix.append(Direction_Matrix_Row(nodes[index], self.NUM_NODES))



        #create direction_matrix
        for row in direction_matrix:

            first_direction = directions_in_map[road_data["direction1_index_in_map"]]
            second_direction = directions_in_map[road_data["direction2_index_in_map"]]
            length = road_data["length"]
            max_speed = road_data["max_speed"]
            road = Road(road_name, first_direction, second_direction, length, max_speed)
            first_direction.set_road(road)
            second_direction.set_road(road)
            edges.append(road)

        # apply layout
        self.force_directed_layout(nodes, edges)

        # create vehicles


        # create graph
        self.graph = Graph(nodes, edges, vehicles)

        # set vehicles' paths
        for vehicle in self.graph.vehicles:
            vehicle.set_path(self.graph)

        return self.graph
    """

    def force_directed_layout(self, nodes, edges):
        G = nx.Graph()
        node_id_map = {node: idx for idx, node in enumerate(nodes)}
        id_node_map = {idx: node for node, idx in node_id_map.items()}
        for edge in edges:
            src, dst = edge.first_direction.parent_junction, edge.second_direction.parent_junction
            if src != dst:
                G.add_edge(node_id_map[src], node_id_map[dst])
        pos = nx.spring_layout(G, seed=42)
        padding = 50
        area_width = self.SIMULATION_SCREEN.width - 2 * padding
        area_height = self.SIMULATION_SCREEN.height - 2 * padding
        for node_id, (x, y) in pos.items():
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
                print(f"[DEBUG] Vehicle data loaded from {file_path}")
        except Exception as e:
            print(f"[ERROR] Failed to load vehicle data from JSON: {e}")

    def get_dominant_energy_type(self, vehicle_kind):
        # Just an example heuristic: you can adjust this logic
        # Assign energy types based on percentages or even split rules
        electric = self.vehicle_stats.get("Electric", 0)
        gasoline = self.vehicle_stats.get("Gasoline", 0)
        gas = self.vehicle_stats.get("Gas", 0)

        energies = {"Electric": electric, "Gasoline": gasoline, "Gas": gas}
        dominant = max(energies.items(), key=lambda x: x[1])[0]
        return dominant

    def collect_consumption_statistics(self, graph):
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
