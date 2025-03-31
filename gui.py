# === File: gui.py ===
import pygame
from simulation import Simulation

# --- Config ---
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 600
ROAD_HEIGHT = 40
CAR_WIDTH = 30
CAR_HEIGHT = 20
TICK_DURATION = 800  # ms
PIXELS_PER_STEP = 50
RECENTLY_DONE_DURATION = 1  # show car for 1 extra tick

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (180, 180, 180)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
BLUE = (50, 100, 255)

# Pygame setup
pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("GreenWave Simulation - Turning")
clock = pygame.time.Clock()

# Run simulation
sim = Simulation()
sim.setup()

# Y-position map for junctions (for drawing)
junction_y_map = {
    "A": 150,
    "B": 150,
    "C": 150,
    "D": 300
}

# X-position map (used for traffic light offsets)
junction_x_map = {
    "A": 50,
    "B": 300,
    "C": 550,
    "D": 300
}

# Keep track of recently completed vehicles
recently_done = {}

running = True
while running:
    screen.fill(WHITE)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if sim.tick % 3 == 0:
        new_vehicle = sim.create_vehicle()
        if new_vehicle:
            sim.vehicles.append(new_vehicle)

    for junction in sim.junctions:
        junction.update_traffic_lights()

    for vehicle in sim.vehicles:
        if not vehicle.done:
            vehicle.move()
        elif vehicle.id not in recently_done:
            recently_done[vehicle.id] = sim.tick

    for road in sim.roads:
        start_x = junction_x_map[road.start.name]
        start_y = junction_y_map[road.start.name]
        end_x = junction_x_map[road.end.name]
        end_y = junction_y_map[road.end.name]

        if start_y == end_y:
            pygame.draw.rect(screen, GRAY, (start_x, start_y, end_x - start_x, ROAD_HEIGHT))
        else:
            top = min(start_y, end_y)
            height = abs(end_y - start_y)
            pygame.draw.rect(screen, GRAY, (start_x + 20, top, ROAD_HEIGHT, height))

    for junction in sim.junctions[1:]:
        x = junction_x_map[junction.name]
        y = junction_y_map[junction.name]
        state = junction.traffic_light.state
        color = GREEN if state == "green" else RED if state == "red" else YELLOW
        pygame.draw.circle(screen, color, (x + 10, y - 15), 10)

    for vehicle in sim.vehicles:
        show = not vehicle.done or (vehicle.id in recently_done and sim.tick - recently_done[vehicle.id] <= RECENTLY_DONE_DURATION)
        if not show:
            continue

        try:
            if vehicle.done:
                final_road = vehicle.route[-1]
                end_x = junction_x_map[final_road.end.name]
                end_y = junction_y_map[final_road.end.name]
                start_y = junction_y_map[final_road.start.name]

                if start_y == end_y:
                    # Horizontal road
                    x = end_x - CAR_WIDTH - 5
                    y = end_y + (ROAD_HEIGHT - CAR_HEIGHT) // 2
                    pygame.draw.rect(screen, BLUE, (x, y, CAR_WIDTH, CAR_HEIGHT))
                    font = pygame.font.SysFont(None, 18)
                    id_text = font.render(f"#{vehicle.id}", True, BLACK)
                    screen.blit(id_text, (x + 5, y - 15))
                else:
                    # Vertical road
                    x = end_x + (ROAD_HEIGHT - CAR_HEIGHT) // 2
                    y = end_y - CAR_WIDTH - 5
                    pygame.draw.rect(screen, BLUE, (x, y, CAR_HEIGHT, CAR_WIDTH))
                    font = pygame.font.SysFont(None, 18)
                    id_text = font.render(f"#{vehicle.id}", True, BLACK)
                    screen.blit(id_text, (x - 20, y + 5))
            else:
                if vehicle.current_road_index < len(vehicle.route):
                    road = vehicle.route[vehicle.current_road_index]
                    start_x = junction_x_map[road.start.name]
                    start_y = junction_y_map[road.start.name]
                    end_x = junction_x_map[road.end.name]
                    end_y = junction_y_map[road.end.name]

                    max_steps = abs(end_x - start_x) // PIXELS_PER_STEP if start_y == end_y else abs(end_y - start_y) // PIXELS_PER_STEP
                    pos = min(vehicle.position, max_steps)

                    if start_y == end_y:
                        x = start_x + pos * PIXELS_PER_STEP
                        y = start_y + (ROAD_HEIGHT - CAR_HEIGHT) // 2
                        pygame.draw.rect(screen, BLUE, (x, y, CAR_WIDTH, CAR_HEIGHT))
                        font = pygame.font.SysFont(None, 18)
                        id_text = font.render(f"#{vehicle.id}", True, BLACK)
                        screen.blit(id_text, (x + 5, y - 15))
                    else:
                        y = start_y + pos * PIXELS_PER_STEP
                        x = start_x + (ROAD_HEIGHT - CAR_HEIGHT) // 2
                        pygame.draw.rect(screen, BLUE, (x, y, CAR_HEIGHT, CAR_WIDTH))
                        font = pygame.font.SysFont(None, 18)
                        id_text = font.render(f"#{vehicle.id}", True, BLACK)
                        screen.blit(id_text, (x - 20, y + 5))
        except IndexError:
            continue

    font = pygame.font.SysFont(None, 24)
    tick_label = font.render(f"Tick: {sim.tick}", True, BLACK)
    screen.blit(tick_label, (10, 10))

    pygame.display.flip()
    pygame.time.delay(TICK_DURATION)
    sim.tick += 1

pygame.quit()
