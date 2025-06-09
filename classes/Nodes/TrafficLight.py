from typing import Set

from classes.Nodes.Lane import Lane
from classes.Enums.State import State, STATE_SIZE
from screens.functions import are_there_possible_collisions, get_blocked_traffic_lights_by_traffic_lights, \
    get_blocked_traffic_lights_by_traffic_light


def check_traffic_light_validity(lanes):  # lanes: list[Lane]
    """
    Checks whether the values are valid (e.g. no future overflows nor possible collisions)
    each lane of a traffic light is sorted from right (index 0) to left (index len(lanes) - 1)
    """
    if not isinstance(lanes, list):
        raise TypeError("Traffic Light is invalid: Not a list parameter was given")
    size = 0
    for lane in lanes:
        if not isinstance(lane, Lane):
            raise TypeError("Traffic Light is invalid: Non-Lane value")
        size += 1
    if not (size >= 1):
        raise TypeError("Traffic Light is invalid: Not enough lanes")
    if are_there_possible_collisions(lanes):
        raise TypeError("Traffic Light is invalid: Possible collisions detected")
    return True


class TrafficLight:

    def __init__(self, key, lanes=None):
        self.key = key
        self.lanes = None
        self.size = None
        self.current_state = None
        self.set_lanes(lanes)

    def set_lanes(self, lanes):
        if None is lanes:
            return False
        try:
            check_traffic_light_validity(lanes)
            self.lanes = lanes
            self.size = len(lanes)
        except Exception as e:
            print(f"Traffic Light couldn't be created due to this error: {e}")
            return False
        return True

    def set_state(self, state):
        if not isinstance(state, State):
            return False
        self.current_state = state
        for lane in self.lanes:
            lane.set_cur_state(self.current_state)
        return True

    def update_state(self):
        self.current_state = State((self.current_state.value + 1) % STATE_SIZE)
        for lane in self.lanes:
            lane.update_state()

    def get_direction(self):
        if None is self.lanes:
            return None
        return self.lanes[0].parent_direction

    def get_directions_directing_indexes(self):
        directions_directing_indexes = set()
        for lane in self.lanes:
            for to_lane in lane.to_lanes:
                directions_directing_indexes.add(to_lane.parent_direction.module_index)
        return list(directions_directing_indexes)

    def get_minimum_to_lane_index_by_direction(self, direction):
        indexes = []
        for lane in self.lanes:
            for to_lane in lane.to_lanes:
                if to_lane.parent_direction is direction:
                    indexes.append(to_lane.index_in_junction)
        if indexes:
            return min(indexes)
        return float('inf')

    def get_maximum_to_lane_index_by_direction(self, direction):
        indexes = []
        for lane in self.lanes:
            for to_lane in lane.to_lanes:
                if to_lane.parent_direction is direction:
                    indexes.append(to_lane.index_in_junction)
        if indexes:
            return max(indexes)
        return -1

    def get_weight(self, included: Set['TrafficLight'], junction) -> int:
        blocked_traffic_lights_by_self = get_blocked_traffic_lights_by_traffic_light(junction, self)
        blocked_traffic_lights_by_included = get_blocked_traffic_lights_by_traffic_lights(junction, included)

        blocked_traffic_lights_for_weight = blocked_traffic_lights_by_self - blocked_traffic_lights_by_included
        weight = 0
        for traffic_light in blocked_traffic_lights_for_weight:
            weight += traffic_light.size
        return weight

    def __repr__(self):
        return self.key
    def __eq__(self, other):
        return isinstance(other, TrafficLight) and self.key == other.key

    def __hash__(self):
        return hash(self.key)
