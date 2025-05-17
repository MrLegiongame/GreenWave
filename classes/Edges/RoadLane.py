from classes.Entities.Vehicles.Vehicle import Vehicle


def check_road_lane_validity(parent_road, source_lane, destination_lane, length):
    from classes.Nodes.Lane import Lane
    from classes.Edges.Road import Road
    if not isinstance(parent_road, Road):
        raise TypeError("RoadLane is invalid: Non-Road value was given")
    if not isinstance(source_lane, Lane):
        raise TypeError("RoadLane is invalid: Non-Direction value was given")
    if not isinstance(destination_lane, Lane):
        raise TypeError("RoadLane is invalid: Non-Direction value was given")
    if not isinstance(length, int):
        raise TypeError("RoadLane is invalid: Non-int value was given")
    if not (length > 0):
        raise TypeError("RoadLane is invalid: length with non-positive value")
    return True


class RoadLane:
    def __init__(self, parent_road, source_lane, destination_lane, length):
        self.parent_road = None
        self.source_lane = None
        self.destination_lane = None
        self.length = None
        self.vehicles = []
        self.vehicles_size = 0

        try:
            check_road_lane_validity(parent_road, source_lane, destination_lane, length)
            self.parent_road = parent_road
            self.source_lane = source_lane
            self.source_lane.road_lane = self
            self.destination_lane = destination_lane
            self.destination_lane.road_lane = self
            self.length = length
        except TypeError as e:
            print(f"RoadLane couldn't be created due to this error: {e}")

    def vehicle_enter_lane(self, vehicle):
        if not isinstance(vehicle, Vehicle):
            return False

        closest_distance_behind = float('inf')  # infinity
        closest_distance_after = float('inf')  # infinity
        order = 0

        for v in range(self.vehicles_size):
            # TODO finish the loop
            distance_between = vehicle.distance_on_road_lane - self.vehicles[v].distance_on_road_lane
            if distance_between < closest_distance_behind and vehicle.distance_on_road_lane > self.vehicles[v].distance_on_road_lane:
                closest_distance_behind = distance_between

            distance_between = self.vehicles[v].distance_on_road_lane - vehicle.distance_on_road_lane
            if distance_between < closest_distance_after and vehicle.distance_on_road_lane < self.vehicles[v].distance_on_road_lane:
                closest_distance_after = distance_between

        vehicle.road_lane = self
        self.vehicles.insert(order, vehicle)
        self.vehicles_size += 1
        return True

    def vehicle_leave_lane(self, vehicle):
        if not isinstance(vehicle, Vehicle):
            return False
        for v in self.vehicles:
            if v is vehicle:
                vehicle.road_lane = None
                self.vehicles.remove(vehicle)
                self.vehicles_size -= 1
                return True
        return False
