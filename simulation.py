import time
from entities.road import Road
import random
from entities.lane import Lane
from entities.vehicle import Vehicle
from entities.junction import Junction
from entities.traffic_light import TrafficLight


class Simulation:
    def __init__(self):
        self.junctions = []
        self.vehicles = []
        self.roads = []  # Add this to store all roads
        self.tick = 0

    def setup(self):
        # Create junctions
        jA = Junction("A")
        jB = Junction("B")
        jC = Junction("C")
        jD = Junction("D")

        # Create roads
        roadAB = Road(jA, jB)
        roadBC = Road(jB, jC)
        roadBD = Road(jB, jD)  # This is the “turn”

        # Link roads to junctions
        jA.add_outgoing_road(roadAB)
        jB.add_incoming_road(roadAB)

        jB.add_outgoing_road(roadBC)
        jC.add_incoming_road(roadBC)

        jB.add_outgoing_road(roadBD)
        jD.add_incoming_road(roadBD)

        # Register all
        self.junctions = [jA, jB, jC, jD]
        self.roads = [roadAB, roadBC, roadBD]

    def create_vehicle(self):
        if len(self.roads[0].lanes[0].vehicles) < 10:
            # Randomly decide where the vehicle goes after B
            if random.random() < 0.5:
                route = [self.roads[0], self.roads[1]]  # A → B → C
            else:
                route = [self.roads[0], self.roads[2]]  # A → B → D

            v = Vehicle(vehicle_type="car", route=route)
            route[0].lanes[0].add_vehicle(v)
            print(f"Spawned Vehicle #{v.id} → {[r.end.name for r in route]}")
            return v
        return None

    def run(self, duration=20):
        self.setup()
        for _ in range(duration):
            print(f"\n--- TICK {self.tick} ---")

            # Spawn a new vehicle every 3 ticks
            # if self.tick % 3 == 0:
            #     new_vehicle = Vehicle(vehicle_type="car", route=[self.junctions[0].outgoing_roads[0]])
            #     self.junctions[0].outgoing_roads[0].lanes[0].add_vehicle(new_vehicle)
            #     self.vehicles.append(new_vehicle)
            #     print("Spawned a new vehicle")

            for j in self.junctions:
                j.update_traffic_lights()

            for v in self.vehicles:
                if not v.done:
                    v.move()
                    # After vehicle moves, print lane state
                    lane = self.junctions[0].outgoing_roads[0].lanes[0]
                    print(f"Lane state: {[f'#{v.id}:{v.position}' for v in lane.vehicles if not v.done]}")

            self.tick += 1
            time.sleep(0.5)

            if self.tick == duration - 1:
                completed = [v for v in self.vehicles if v.done]
                if completed:
                    avg_wait = sum(v.wait_time for v in completed) / len(completed)
                    print(f"\nAverage wait time for {len(completed)} vehicles: {avg_wait:.2f} ticks")


if __name__ == "__main__":
    sim = Simulation()
    sim.run()