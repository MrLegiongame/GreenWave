import math
import random

import networkx as nx
import pygame
import sys
import tkinter as tk

from classes.Edges.Road import Road
from classes.Entities.Graph import Graph
from classes.Entities.Point import Point
from classes.Entities.Vehicles.Car import Car
from classes.Entities.Vehicles.Engine import Engine
from classes.Entities.Vehicles.Vehicle import get_image_list
from classes.Enums.Color import Color
from classes.Entities.Simulation import Simulation
from classes.Enums.EdgeDensity import EdgeDensity
from classes.Nodes.Direction import Direction
from classes.Nodes.Junction import Junction

# === Global variables ===
global running, is_stopped, SCREEN, SIMULATION_SCREEN, CONTROL_BAR_SCREEN, JUNCTION_SCREEN, VEHICLE_SCREEN, FPS


root = tk.Tk()
root.withdraw()  # Hide the window

# === Constants ===

# Set window dimensions
WINDOW_WIDTH = root.winfo_screenwidth() - 100
WINDOW_HEIGHT = root.winfo_screenheight() - 100

# Define screen sizes
MAIN_WIDTH = (2 * WINDOW_WIDTH) // 3  # Left main screen
MAIN_HEIGHT = (9 * WINDOW_HEIGHT) // 10
SIDE_WIDTH = WINDOW_WIDTH - MAIN_WIDTH  # Right side area
SIDE_HEIGHT = (WINDOW_HEIGHT // 2)  # Each of the screens' height
CONTROL_BAR_HEIGHT = WINDOW_HEIGHT - MAIN_HEIGHT

# Define dividers' width
DIVIDER_WIDTH = 2

# Define button
BUTTON_CENTER = Point((MAIN_WIDTH // 2), MAIN_HEIGHT + (CONTROL_BAR_HEIGHT // 2))  # x, y (center of the circle)
BUTTON_RADIUS = 25

# Define graph settings
FPS = 60
NUM_NODES = 25
NUM_CARS = 20
EDGES_DENSITY = random.choice((EdgeDensity.LOW, EdgeDensity.MEDIUM, EdgeDensity.HIGH))
CAR_SPEED = 2
EDGE_WIDTH = 2
NODE_RADIUS = 6
CAR_RADIUS = 5
EDGE_COLOR = Color.DARK_GREY
NODE_COLOR = Color.LIGHT_GREY
CAR_COLOR = Color.RED
BACKGROUND = Color.BLACK


# === Functions ===

def exit_button_pressed():
    global running
    running = False


# Button function
def stop_button_pressed():
    global is_stopped
    is_stopped = not is_stopped


def is_cursor_in_circle(center_point, radius):
    mouse_pos = pygame.mouse.get_pos()
    dx = mouse_pos[0] - center_point.x
    dy = mouse_pos[1] - center_point.y
    distance_squared = dx ** 2 + dy ** 2

    return distance_squared <= radius ** 2


def setup_window():
    global running, is_stopped, SCREEN, SIMULATION_SCREEN, CONTROL_BAR_SCREEN, JUNCTION_SCREEN, VEHICLE_SCREEN

    # Initialize Pygame
    pygame.init()
    pygame.display.set_caption("GreenWave - Simulation")

    # === Initialize global variables ===

    # Initialize booleans
    running = True
    is_stopped = False

    # Create the window
    SCREEN = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

    # Define rectangles for each screen area
    SIMULATION_SCREEN = pygame.Rect(0, 0, MAIN_WIDTH, MAIN_HEIGHT)
    CONTROL_BAR_SCREEN = pygame.Rect(0, MAIN_HEIGHT, MAIN_WIDTH, CONTROL_BAR_HEIGHT)
    JUNCTION_SCREEN = pygame.Rect(MAIN_WIDTH, 0, SIDE_WIDTH, SIDE_HEIGHT)
    VEHICLE_SCREEN = pygame.Rect(MAIN_WIDTH, SIDE_HEIGHT, SIDE_WIDTH, SIDE_HEIGHT)


def handle_events(sim):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit_button_pressed()
        # Detect mouse click event
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
            if is_cursor_in_circle(BUTTON_CENTER, BUTTON_RADIUS):  # If mouse clicked on stop-button
                stop_button_pressed()
            else:
                for junction in sim.graph.nodes:
                    if is_cursor_in_circle(junction.point, NODE_RADIUS):
                        sim.set_current_junction(junction)
                        return
                for vehicle in sim.graph.vehicles:
                    if is_cursor_in_circle(vehicle.cur_point, CAR_RADIUS):
                        sim.set_current_vehicle(vehicle)
                        return


def run_simulation(sim):
    global is_stopped
    if is_stopped:
        return
    # TODO


def draw_graph(sim):
    global SCREEN
    if None is sim.graph:
        return
    sim.graph.draw(SCREEN, sim)


def draw_regular_polygon(surface, center, radius, num_sides, width=0, draw_normals=False, normal_length=40):
    two_sides_flag = (2 == num_sides)
    if two_sides_flag:  # for 2-directions junction
        num_sides = 4

    angle_step = 2 * math.pi / num_sides
    points = []

    # Step 1: Calculate polygon vertices
    for i in range(num_sides):
        angle = i * angle_step - math.pi / 2  # Start at top
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        points.append((x, y))

    # Step 2: Draw the polygon
    pygame.draw.polygon(surface, Color.GREY.value, points, width)

    steps = 1
    if two_sides_flag:  # for 2-directions junction
        steps = 2

    # Step 3: Draw normals (if enabled)
    if draw_normals:
        for i in range(0, num_sides, steps):
            p1 = points[i]
            p2 = points[(i + 1) % num_sides]

            # Midpoint of the side
            mid_x = (p1[0] + p2[0]) / 2
            mid_y = (p1[1] + p2[1]) / 2

            # Direction vector (dx, dy)
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]

            # Orthogonal direction (rotate 90 degrees CW for outward)
            ortho_dx = dy
            ortho_dy = -dx

            # Normalize
            length = math.hypot(ortho_dx, ortho_dy)
            ortho_dx /= length
            ortho_dy /= length

            # End point of the normal line
            end_x = mid_x + ortho_dx * normal_length
            end_y = mid_y + ortho_dy * normal_length

            # Draw the line
            pygame.draw.line(surface, Color.WHITE.value, (mid_x, mid_y), (end_x, end_y), 2)


def draw_junction(sim):
    global SCREEN
    if None is sim.current_junction:
        return
    center = (WINDOW_WIDTH - (SIDE_WIDTH // 2), SIDE_HEIGHT // 2)
    num_sides = sim.current_junction.size
    draw_regular_polygon(SCREEN, center=center, radius=90, num_sides=num_sides, draw_normals=True)
    # TODO
    pass


def draw_vehicle(sim):
    global SCREEN
    if None is sim.current_vehicle:
        return
    # TODO
    pass


def draw_layout(sim):
    global is_stopped, SCREEN, SIMULATION_SCREEN, CONTROL_BAR_SCREEN, JUNCTION_SCREEN, VEHICLE_SCREEN, FPS

    clock = pygame.time.Clock()

    # Fill background
    SCREEN.fill(Color.WHITE.value)

    # Draw each screen area
    pygame.draw.rect(SCREEN, Color.VERY_DARK_GREY.value, SIMULATION_SCREEN)  # Simulation screen
    pygame.draw.rect(SCREEN, Color.VERY_DARK_GREY.value, CONTROL_BAR_SCREEN)  # Control bar screen
    pygame.draw.rect(SCREEN, Color.VERY_DARK_GREY.value, JUNCTION_SCREEN)  # Junction screen
    pygame.draw.rect(SCREEN, Color.VERY_DARK_GREY.value, VEHICLE_SCREEN)  # Vehicle screen

    # Draw dividers
    pygame.draw.line(SCREEN, Color.LIGHT_GREY.value, (0, MAIN_HEIGHT), (MAIN_WIDTH, MAIN_HEIGHT), DIVIDER_WIDTH)
    pygame.draw.line(SCREEN, Color.LIGHT_GREY.value, (MAIN_WIDTH, 0), (MAIN_WIDTH, WINDOW_HEIGHT), DIVIDER_WIDTH)
    pygame.draw.line(SCREEN, Color.LIGHT_GREY.value, (MAIN_WIDTH, SIDE_HEIGHT), (WINDOW_WIDTH, SIDE_HEIGHT), DIVIDER_WIDTH)

    # Determine stop-button's colors
    if is_cursor_in_circle(BUTTON_CENTER, BUTTON_RADIUS):  # Cursor is inside the button
        current_button_color = Color.DARK_RED
        current_text_color = Color.GREY
    else:   # Cursor is outside the button
        current_button_color = Color.RED
        current_text_color = Color.WHITE

    # Draw the circular button
    pygame.draw.circle(SCREEN, current_button_color.value, (BUTTON_CENTER.x, BUTTON_CENTER.y), BUTTON_RADIUS)

    # Draw text centered in the circle
    if is_stopped:
        current_text = ">"
    else:
        current_text = "| |"
    font = pygame.font.SysFont("Arial", 30)
    text_surface = font.render(current_text, True, current_text_color.value)
    text_rect = text_surface.get_rect(center=(BUTTON_CENTER.x, BUTTON_CENTER.y))
    SCREEN.blit(text_surface, text_rect)

    # Draw each screen's content
    draw_graph(sim)
    draw_junction(sim)
    draw_vehicle(sim)

    # Update the display
    pygame.display.flip()
    clock.tick(FPS)


def force_directed_layout(nodes, edges):
    # ======== Apply Force-Directed Layout to place junctions visually ========
    G = nx.Graph()

    # Map junctions to unique IDs for NetworkX
    node_id_map = {node: idx for idx, node in enumerate(nodes)}
    id_node_map = {idx: node for node, idx in node_id_map.items()}

    # Build the graph from the edges
    for edge in edges:
        src = edge.source_direction.parent_junction
        dst = edge.destination_direction.parent_junction
        if src != dst:
            G.add_edge(node_id_map[src], node_id_map[dst])

    # Compute layout (normalized in range [-1, 1])
    pos = nx.spring_layout(G, seed=42)

    # Scale layout to screen size (simulation area)
    padding = 50
    area_width = SIMULATION_SCREEN.width - 2 * padding
    area_height = SIMULATION_SCREEN.height - 2 * padding

    for node_id, (x, y) in pos.items():
        screen_x = int(padding + (x + 1) / 2 * area_width)
        screen_y = int(padding + (y + 1) / 2 * area_height)
        id_node_map[node_id].point = Point(screen_x, screen_y)


def set_graph(sim):
    junctions = []
    edges = []
    vehicles = []
    roads_amount = 3
    name = 1

    # creating nodes
    for node in range(NUM_NODES):
        junctions.append(Junction())

    # creating directions for nodes
    for junction in junctions:

        chance = random.random()
        if EdgeDensity.LOW == EDGES_DENSITY:
            if chance < 0.1:  # 10%
                roads_amount = 2
            elif chance < 0.85:  # 75%
                roads_amount = 3
            else:  # 15%
                roads_amount = 4
        elif EdgeDensity.MEDIUM == EDGES_DENSITY:
            if chance < 0.02:  # 2%
                roads_amount = 2
            elif chance < 0.47:  # 45%
                roads_amount = 3
            elif chance < 0.97:  # 50%
                roads_amount = 4
            else:  # 3%
                roads_amount = 5
        elif EdgeDensity.HIGH == EDGES_DENSITY:
            if chance < 0.15:  # 15%
                roads_amount = 3
            elif chance < 0.95:  # 80%
                roads_amount = 4
            else:  # 5%
                roads_amount = 5

        for edge in range(roads_amount):
            junction.add_direction(Direction())
            junction.directions[edge].set_parent_junction(junction)  # sets parent-junction for direction

    # creating roads
    for junction in junctions:

        filtered_list = [x for x in junctions if x != junction]

        for direction in junction.directions:
            destination_direction = random.choice(random.choice(filtered_list).directions)
            length = random.randint(100, 800)
            lanes_size = random.randint(1, 3)
            edges.append(Road(str(name), direction, destination_direction, length))
            edges.append(Road(str(name), destination_direction, direction, length))
            name += 1

    force_directed_layout(junctions, edges)

    # creating vehicles
    for vehicle in range(NUM_CARS):
        src_road = random.choice(edges)

        excluded = src_road
        filtered_list = [x for x in edges if x != excluded]

        dst_road = random.choice(filtered_list)

        weight = random.randint(1200, 2400)
        image = random.choice(get_image_list("images/vehicles/cars"))

        vehicles.append(Car(2, Engine(3, "Gas"), weight, src_road, dst_road, image))

    sim.graph = Graph(junctions, edges, vehicles)

    # sets paths
    for vehicle in vehicles:
        vehicle.set_path(sim.graph)


def handle_simulation(json):
    global running
    sim = Simulation(json)
    set_graph(sim)
    while running:
        handle_events(sim)
        run_simulation(sim)
        draw_layout(sim)
    pygame.quit()
    sys.exit()


def main():
    json = None
    setup_window()
    handle_simulation(json)


main()
