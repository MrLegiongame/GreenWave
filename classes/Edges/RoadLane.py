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

    def get_list_of_vehicles_which_are_left_with_more_than_one_junction_sorted_by_arrival_time_from_and_to_seconds(self, from_seconds, to_seconds):
        res = []
        vehicles = self.get_list_of_vehicles_sorted_by_arrival_time_from_and_to_seconds(from_seconds, to_seconds)
        for vehicle in vehicles:
            if not vehicle.is_next_lane_the_final_lane():
                res.append(vehicle)
        return res

    def get_list_of_vehicles_sorted_by_arrival_time_from_and_to_seconds(self, from_seconds, to_seconds):
        """
        res = []
        for vehicle in self.vehicles:
            if vehicle.is_away_from_next_junction_by_between_start_and_end_seconds(from_seconds, to_seconds):
                res.append(vehicle)
        if not res:
            return res
        return res.sort()
        """
        return sorted(self.vehicles, key=lambda obj: getattr(obj, "is_away_from_next_junction_by_between_start_and_end_seconds")(from_seconds, to_seconds))

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
