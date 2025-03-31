class Vehicle:
    _id_counter = 1

    def __init__(self, vehicle_type, route):
        self.vehicle_type = vehicle_type
        self.route = route
        self.current_road_index = 0
        self.position = 0
        self.done = False
        self.id = Vehicle._id_counter
        Vehicle._id_counter += 1
        self.wait_time = 0

    def move(self):
        if self.done:
            return

        if self.current_road_index >= len(self.route):
            print(f"Vehicle #{self.id} ({self.vehicle_type}) reached destination with {self.wait_time} ticks of waiting")
            self.done = True
            return

        current_road = self.route[self.current_road_index]
        lane = current_road.lanes[0]

        # Check if someone is directly ahead of me
        for other in lane.vehicles:
            if other != self and not other.done and other.current_road_index == self.current_road_index:
                if other.position == self.position + 1:
                    print(f"Vehicle #{self.id} is waiting behind Vehicle #{other.id}")
                    return

        next_junction = current_road.end

        if self.position >= 3:
            light = next_junction.traffic_light
            if light.state in ["red", "yellow"]:
                print(f"Vehicle #{self.id} waiting at red light at junction {next_junction.name}")
                self.wait_time += 1
                return

            print(f"Vehicle #{self.id} passed through green light at junction {next_junction.name}")
            self.position = 0
            self.current_road_index += 1
        else:
            print(f"Vehicle #{self.id} moving on road from {current_road.start.name} to {current_road.end.name}")
            self.position += 1
