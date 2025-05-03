import pygame
import random
import math
import networkx as nx

from classes.Enums.EdgeDensity import EdgeDensity

# === Colors ===
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_GREY = (100, 100, 100)
BRIGHT_GREY = (200, 200, 200)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# === Pygame setup ===
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("GreenWave - Simulation")
clock = pygame.time.Clock()
FPS = 60

# === Graph setup ===
NUM_NODES = 25
NUM_CARS = 20
EDGES_DENSITY = random.choice((EdgeDensity.LOW, EdgeDensity.MEDIUM, EdgeDensity.HIGH))
CAR_SPEED = 2
EDGE_WIDTH = 2
NODE_RADIUS = 6
CAR_RADIUS = 5
EDGE_COLOR = DARK_GREY
NODE_COLOR = BRIGHT_GREY
CAR_COLOR = RED
BACKGROUND = BLACK

# Create a random graph using NetworkX
lower_limit = int((NUM_NODES ** 2 - NUM_NODES) * ((EDGES_DENSITY.value - 1) / 3))
higher_limit = int((NUM_NODES ** 2 - NUM_NODES) * (EDGES_DENSITY.value / 3))
NUM_EDGES = random.randint(lower_limit, higher_limit)

G = nx.gnm_random_graph(NUM_NODES, NUM_EDGES)
while not nx.is_connected(G):  # ensure the graph is connected
    G = nx.gnm_random_graph(NUM_NODES, NUM_EDGES)

# Force-directed layout (Fruchterman-Reingold)
pos = nx.spring_layout(G, seed=42)  # Force-directed layout
# Normalize to screen coordinates
for node in pos:
    x, y = pos[node]
    pos[node] = (
        int((x + 1) * WIDTH / 2),
        int((y + 1) * HEIGHT / 2)
    )

edges = list(G.edges())
edge_weights = {edge: random.randint(1, 10) for edge in edges}


# --- Helpers ---
def distance(p1, p2):
    return math.hypot(p2[0]-p1[0], p2[1]-p1[1])


def unit_vector(p1, p2):
    d = distance(p1, p2)
    return (p2[0]-p1[0])/d, (p2[1]-p1[1])/d if d != 0 else (0, 0)


# --- Car class ---
class Car:
    def __init__(self, path):
        self.path = path
        self.current = 0
        self.pos = list(pos[path[0]])
        self.target = pos[path[1]]
        self.vx, self.vy = unit_vector(self.pos, self.target)

    def update(self):
        self.pos[0] += self.vx * CAR_SPEED
        self.pos[1] += self.vy * CAR_SPEED
        if distance(self.pos, self.target) < CAR_SPEED:
            self.current += 1
            if self.current >= len(self.path) - 1:
                self.current = 0
                self.pos = list(pos[self.path[0]])
            self.target = pos[self.path[self.current + 1]]
            self.vx, self.vy = unit_vector(self.pos, self.target)

    def draw(self, surface):
        pygame.draw.circle(surface, CAR_COLOR, (int(self.pos[0]), int(self.pos[1])), CAR_RADIUS)


# --- Path Generator ---
def random_path():
    start = random.choice(list(G.nodes))
    path = [start]
    for _ in range(random.randint(3, 6)):
        neighbors = list(G.neighbors(path[-1]))
        if not neighbors:
            break
        next_node = random.choice(neighbors)
        if next_node not in path:
            path.append(next_node)
    return path


def draw_regular_polygon(surface, color, center, radius, num_sides, width=0):
    angle_step = 2 * math.pi / num_sides
    points = []

    for i in range(num_sides):
        angle = i * angle_step - math.pi / 2  # Start at top (rotate -90°)
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        points.append((x, y))

    pygame.draw.polygon(surface, color, points, width)


pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

# Create cars
vehicles = [Car(random_path()) for _ in range(NUM_CARS)]

# === Main loop ===
running = True
while running:
    screen.fill(BACKGROUND)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Draw edges
    for u, v in G.edges():
        pygame.draw.line(screen, EDGE_COLOR, pos[u], pos[v], EDGE_WIDTH)

    # Draw nodes
    for node in G.nodes:
        pygame.draw.circle(screen, NODE_COLOR, pos[node], NODE_RADIUS)

    # Update + draw cars
    for car in vehicles:
        car.update()
        car.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
