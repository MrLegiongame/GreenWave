from entities.traffic_light import TrafficLight

class Junction:
    def __init__(self, name):
        self.name = name
        self.incoming_roads = []
        self.outgoing_roads = []
        self.traffic_light = TrafficLight()

    def add_incoming_road(self, road):
        self.incoming_roads.append(road)

    def add_outgoing_road(self, road):
        self.outgoing_roads.append(road)

    def update_traffic_lights(self):
        self.traffic_light.update()