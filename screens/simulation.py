import json
import math
import random
import networkx as nx
import pygame
import sys
import tkinter as tk

from classes.Edges.Road import Road
from classes.Entities.Graph import Graph, load_graph_from_json
from classes.Entities.Point import Point
from classes.Entities.Vehicles.Car import Car
from classes.Entities.Vehicles.Engine import Engine
from classes.Entities.Vehicles.Vehicle import get_image_list
from classes.Enums.Color import Color
from classes.Entities.Simulation import Simulation
from classes.Enums.EdgeDensity import EdgeDensity
from classes.Nodes.Direction import Direction
from classes.Nodes.Junction import Junction


class SimulationScreen:
    def __init__(self, screen, ui_manager):
        self.screen = screen
        self.ui_manager = ui_manager
        self.next_screen = None
        self.sim = Simulation(None)
        self.running = True
        self.is_stopped = False
        self.clock = pygame.time.Clock()

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

        self.set_graph()

    def get_next_screen(self):
        return self.next_screen

    def handle_events(self, event):
        if event.type == pygame.QUIT:
            print("[EVENT] Quit event received.")
            self.running = False
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            print("[EVENT] Mouse click at", pygame.mouse.get_pos())
            if self.is_cursor_in_circle(self.BUTTON_CENTER, self.BUTTON_RADIUS):
                self.is_stopped = not self.is_stopped
                print(f"[EVENT] Simulation {'stopped' if self.is_stopped else 'resumed'}")
            else:
                for junction in self.sim.graph.nodes:
                    if self.is_cursor_in_circle(junction.point, 6):
                        self.sim.set_current_junction(junction)
                        print(f"[EVENT] Junction selected at {junction.point}")
                        return
                for vehicle in self.sim.graph.vehicles:
                    if vehicle.cur_point:
                        x, y = int(vehicle.cur_point.x), int(vehicle.cur_point.y)
                        print(f"[DRAW] Vehicle at ({x}, {y})")
                        # Draw vehicle as a red dot
                        pygame.draw.circle(
                            self.screen,
                            Color.RED,  # Assuming CAR_COLOR = Color.RED
                            (x, y),
                            5  # e.g., 5
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
        if not self.is_stopped:
            print("[UPDATE] Simulation running.")
        else:
            print("[UPDATE] Simulation paused.")

    def draw(self):
        print("[DRAW] Redrawing screen...")
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
        text_surface = font.render(button_text, True, text_color.value)
        text_rect = text_surface.get_rect(center=(self.BUTTON_CENTER.x, self.BUTTON_CENTER.y))
        self.screen.blit(text_surface, text_rect)

        self.draw_graph()
        self.draw_junction()
        self.draw_vehicle()

    def draw_graph(self):
        if self.sim.graph is None:
            return
        self.sim.graph.draw(self.screen, self.sim)

    def draw_junction(self):
        if self.sim.current_junction is None:
            return
        center = (self.WINDOW_WIDTH - (self.SIDE_WIDTH // 2), self.SIDE_HEIGHT // 2)
        num_sides = self.sim.current_junction.size
        self.draw_regular_polygon(self.screen, center, 90, num_sides, draw_normals=True)

    def draw_vehicle(self):
        if self.sim.current_vehicle is None:
            return
        # Placeholder for vehicle details (if needed)

    def draw_regular_polygon(self, surface, center, radius, num_sides, width=0, draw_normals=False, normal_length=40):
        if num_sides == 2:
            num_sides = 4
        angle_step = 2 * math.pi / num_sides
        points = [(center[0] + radius * math.cos(i * angle_step - math.pi / 2),
                   center[1] + radius * math.sin(i * angle_step - math.pi / 2)) for i in range(num_sides)]
        pygame.draw.polygon(surface, Color.GREY.value, points, width)
        if draw_normals:
            for i in range(0, num_sides, 1 if num_sides != 4 else 2):
                p1, p2 = points[i], points[(i + 1) % num_sides]
                mid_x, mid_y = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
                dx, dy = p2[0] - p1[0], p2[1] - p1[1]
                ortho_dx, ortho_dy = dy / math.hypot(dx, dy), -dx / math.hypot(dx, dy)
                end_x, end_y = mid_x + ortho_dx * normal_length, mid_y + ortho_dy * normal_length
                pygame.draw.line(surface, Color.WHITE.value, (mid_x, mid_y), (end_x, end_y), 2)

    def set_graph(self):
        """
        junctions, edges, vehicles = [], [], []
        roads_amount, name = 3, 1

        for _ in range(self.NUM_NODES):
            junctions.append(Junction())
        for junction in junctions:
            chance = random.random()
            roads_amount = 2 if chance < 0.1 else 3 if chance < 0.85 else 4
            if self.EDGES_DENSITY == EdgeDensity.MEDIUM:
                roads_amount = 2 if chance < 0.02 else 3 if chance < 0.47 else 4
            if self.EDGES_DENSITY == EdgeDensity.HIGH:
                roads_amount = 3 if chance < 0.15 else 4
            for _ in range(roads_amount):
                junction.add_direction(Direction())
                junction.directions[-1].set_parent_junction(junction)

        for junction in junctions:
            filtered_list = [x for x in junctions if x != junction]
            for direction in junction.directions:
                destination = random.choice(random.choice(filtered_list).directions)
                length = random.randint(100, 800)
                edges.append(Road(str(name), direction, destination, length))
                edges.append(Road(str(name), destination, direction, length))
                name += 1

        self.force_directed_layout(junctions, edges)

        for _ in range(self.NUM_CARS):
            src_road = random.choice(edges)
            dst_road = random.choice([e for e in edges if e != src_road])
            weight = random.randint(1200, 2400)
            image = random.choice(get_image_list("assets/vehicles/cars"))
            vehicles.append(Car(2, Engine(3, "Gas"), weight, src_road, dst_road, image))
        """

        # self.sim.graph = Graph(junctions, edges, vehicles)
        try:
            with open("map1.json", 'r') as f:
                data = json.load(f)
                self.sim.graph = load_graph_from_json(self, data)
        except Exception as e:
            print(f"[ERROR] Failed to load JSON: {e}")

        """
        for vehicle in vehicles:
            vehicle.set_path(self.sim.graph)
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
