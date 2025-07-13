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

        vehicle.cur_road_lane = self
        vehicle.cur_road_lane_length = self.length
        self.vehicles.append(vehicle)
        self.vehicles_size += 1
        return True

    def vehicle_leave_lane(self, vehicle):
        if not isinstance(vehicle, Vehicle):
            return False
        for v in self.vehicles:
            if v is vehicle:
                vehicle.cur_road_lane = None
                self.vehicles.remove(vehicle)
                self.vehicles_size -= 1
                return True
        return False
