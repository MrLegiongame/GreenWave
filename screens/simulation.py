import json
import math
import random
import networkx as nx
import pygame
import sys
import tkinter as tk
from enum import Enum

from classes.Edges.Road import Road
from classes.Entities.Graph import Graph, find_out_lane_by_index_in_junction
from classes.Entities.Point import Point
from classes.Entities.Vehicles.Vehicle import Vehicle, get_image_list
from classes.Enums.Color import Color
from classes.Entities.Simulation import Simulation
from classes.Enums.EdgeDensity import EdgeDensity
from classes.Enums.LaneFacing import LaneFacing
from classes.Nodes.Direction import Direction
from classes.Nodes.Junction import Junction
from classes.Nodes.Lane import Lane


class SimulationScreen:
    def __init__(self, screen, ui_manager):
        self.screen = screen
        self.ui_manager = ui_manager
        self.next_screen = None
        # self.sim = Simulation(None)
        self.graph = None
        self.current_junction = None
        self.running = True
        self.is_stopped = False
        self.clock = pygame.time.Clock()
        self.dt = 0

        root = tk.Tk()
        root.withdraw()
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
        json_data = json.load(open("map1.json", "r"))
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

    def is_cursor_in_circle(self, center_point, radius):
        mouse_pos = pygame.mouse.get_pos()
        dx = mouse_pos[0] - center_point.x
        dy = mouse_pos[1] - center_point.y
        return (dx ** 2 + dy ** 2) <= radius ** 2

    def update(self, delta_time):
        #print(f"[DEBUG] update() called. is_stopped = {self.is_stopped}")
        self.dt = delta_time
        if not self.is_stopped:
            #print("[UPDATE] Simulation running.")
            for vehicle in self.graph.vehicles:
                vehicle.move(delta_time)
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

        #print(f"[DEBUG] Found {len(self.graph.vehicles)} vehicles in the graph.")

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

        for v in self.graph.vehicles:
            v_type = getattr(v, "vehicle_type", "Unknown")
            energy = getattr(v, "energy_type", "Unknown")

            if v_type in stats and energy in stats[v_type]:
                stats[v_type][energy] += 1
            else:
                print(f"[WARNING] Unexpected vehicle type or energy: {v_type}, {energy}")

        for v_type, counts in stats.items():
            row = [v_type, str(counts["Gas"]), str(counts["Gasoline"]), str(counts["Electric"])]
            for idx, value in enumerate(row):
                rect = pygame.Rect(x_start + sum(column_widths[:idx]), y, column_widths[idx], line_height)
                pygame.draw.rect(self.screen, Color.GREY.value, rect)
                pygame.draw.rect(self.screen, Color.WHITE.value, rect, 1)
                text = font.render(value, True, Color.WHITE.value)
                self.screen.blit(text, (rect.x + 5, rect.y + 5))
            y += line_height

    def draw_regular_polygon(self, surface, center, radius, current_junction, directions, width=0, lane_spacing=10,
                             lane_length=40):

        num_sides = current_junction.size
        #junction_index = current_junction.junction_index if hasattr(current_junction, "index_in_map") else "?"
        #print(current_junction.junction_index)
        label_text = f"Junction {current_junction.junction_index}"
        label_surface = pygame.font.SysFont("arial", 20).render(label_text, True, (255, 255, 255))  # white color

        text_rect = label_surface.get_rect(center=(center[0], center[1] - radius - 20))
        surface.blit(label_surface, text_rect)

        if num_sides == 2:
            num_sides = 4

        angle_step = 2 * math.pi / num_sides
        points = [(center[0] + radius * math.cos(i * angle_step - math.pi / 2),
                   center[1] + radius * math.sin(i * angle_step - math.pi / 2)) for i in range(num_sides)]

        pygame.draw.polygon(surface, Color.GREY.value, points, width)

        for i in range(num_sides):
            p1, p2 = points[i], points[(i + 1) % num_sides]
            direction = directions[i]

            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            edge_length = math.hypot(dx, dy)
            dir_x, dir_y = dx / edge_length, dy / edge_length
            ortho_x, ortho_y = dir_y, -dir_x  # perpendicular outward

            total_lanes = len(direction.in_lanes) + len(direction.out_lanes)
            lane_step = edge_length / (total_lanes + 1)

            # Draw OUT lanes
            for lane_index, lane in enumerate(direction.out_lanes):
                offset = lane_step * (lane_index + 1)
                start_x = p1[0] + dir_x * offset
                start_y = p1[1] + dir_y * offset
                end_x = start_x + ortho_x * lane_length
                end_y = start_y + ortho_y * lane_length
                pygame.draw.line(surface, Color.WHITE.value, (start_x, start_y), (end_x, end_y), 2)

            # Draw IN lanes (same x offset, but direction reversed)
            for lane_index, lane in enumerate(direction.in_lanes):
                offset = lane_step * (lane_index + 1 + len(direction.out_lanes))
                start_x = p1[0] + dir_x * offset
                start_y = p1[1] + dir_y * offset
                end_x = start_x + ortho_x * lane_length
                end_y = start_y + ortho_y * lane_length
                pygame.draw.line(surface, (100, 180, 255), (start_x, start_y), (end_x, end_y), 2)

    def set_graph(self, json_data, dt):
        directions_in_map = []  # sorted by indexes in map

        # Extract junctions as nodes
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
            length = road_data["length"]
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
                src_road = random.choice(edges)
                dst_road = random.choice([e for e in edges if e != src_road])
                weight = random.randint(1200, 2400)
                energy = energy_distribution.pop()
                image = random.choice(get_image_list("assets/vehicles/cars"))
                vehicles.append(Vehicle(
                    length=2,
                    weight=weight,
                    start_road=src_road,
                    end_road=dst_road,
                    image=image,
                    vehicle_type=v_type,
                    energy_type=energy,
                    acceleration=3,  # or adjust per type if needed
                    maximum_speed=100
                ))

        self.graph = Graph(nodes, edges, vehicles, dt)

        for vehicle in self.graph.vehicles:
            vehicle.set_path(self.graph)

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

    class Color(Enum):
        RED = (255, 0, 0)
        LIGHT_BLUE = (100, 180, 255)