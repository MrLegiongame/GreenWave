from classes.Nodes.Lane import Lane
from classes.Enums.State import State, STATE_SIZE
from functions import are_there_possible_collisions


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

    def __init__(self, lanes=None):
        self.lanes = None
        self.size = None
        self.current_state = None

        if None is not lanes:
            self.set_lanes(lanes)

    def set_lanes(self, lanes):
        try:
            check_traffic_light_validity(lanes)
            self.lanes = lanes
            self.size = len(lanes)
        except TypeError as e:
            print(f"Traffic Light couldn't be created due to this error: {e}")

    def set_state(self, state):
        if isinstance(state, State):
            self.current_state = state
            return True
        return False

    def change_state(self):
        self.current_state = (self.current_state.value + 1) % STATE_SIZE
        for lane in self.lanes:
            lane.cur_state = self.current_state
