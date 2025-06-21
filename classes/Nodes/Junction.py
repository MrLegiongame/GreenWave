import time
from typing import Set, List

from classes.Entities.Point import Point
from classes.Enums.State import State
from classes.Nodes.Direction import Direction
from classes.Nodes.TrafficLight import TrafficLight
from screens.functions import solve_custom_knapsack


def check_junction_validity(directions):  # directions: tuple[Direction]
    """
    Checks whether the values are valid (e.g. no future overflows nor possible collisions)
    each lane in a certain direction is sorted from right (index 0) to left (index len(direction) - 1)
    """
    if not isinstance(directions, list):
        raise TypeError("Junction is invalid: Not a tuple parameter was given")
    size = 0
    for direction in directions:
        if not isinstance(direction, Direction):
            raise TypeError("Junction is invalid: Non-Direction value")
        size += 1
    if not (size >= 2):
        raise TypeError("Junction is invalid: Not enough directions")
    return True


class Junction:

    """
    We assume each Junction's inside (of size n; directions) is circular, which means that inside[0] is next to
    both inside[n-1] and inside[1]. The same goes for inside[k] (0<k<n-1) which is next to
    both inside[k-1] and inside[k+1].
    The variable 'outside' stores how many lanes are in each direction's outside side from the junction.
    We assume that the indexes are sorted counter-clockwise relatively to the Junction's directions.
    """

    def __init__(self, directions=None):  # directions: list[Direction]
        self.directions = []
        self.size = 0
        self.traffic_lights = None
        self.available_states = None
        self.states_size = None
        self.active_state = None  # for states management
        self.active_index = None  # the index of active_state in available_states
        self.point = None
        self.junction_index = None

        self.distance = None  # for bfs use only
        self.source_junction = None  # for bfs use only

        if None is not directions:
            try:
                check_junction_validity(directions)
                self.directions = directions
                self.size = len(directions)
                self.__set_junction()
                self.__set_lanes_as_direction_tuple()
                self.set_states()
            except Exception as e:
                print(f"Junction couldn't be created due to this error: {e}")

    def __set_junction(self):
        for direction in self.directions:
            direction.set_parent_junction(self)

    def __set_lanes_as_direction_tuple(self):
        for direction in range(self.size):
            for lane in range(self.directions[direction].size):
                new_lane, index = [None] * self.directions[direction].direction[lane].size, 0
                for to_direction in self.directions[direction].direction[lane].lane:
                    new_lane[index] = self.directions[(to_direction + direction + 1) % self.size]
                    index += 1
                self.directions[direction].set_lane_as_direction_tuple(tuple(new_lane), lane)

    def set_point(self, point):
        if isinstance(point, Point):
            self.point = point

    def add_direction(self, direction):
        if isinstance(direction, Direction):
            self.directions.append(direction)
            self.size += 1
            """
            self.available_states = self.create_states()  # tuple[tuple[Lane]]
            self.states_size = len(self.available_states)
            """

    def get_neighbors_junctions(self):
        neighbors = []
        for direction in self.directions:
            edge = direction.road
            neighbor = edge.first_direction.parent_junction
            if self is neighbor:
                neighbor = edge.second_direction.parent_junction
            neighbors.append([neighbor, edge])
        return neighbors

    def get_road_by_neighbor(self, junction):
        for direction in self.directions:
            neighbor = direction.road.first_direction.parent_junction
            if self is neighbor:
                neighbor = direction.road.second_direction.parent_junction
            if junction is neighbor:
                return direction.road
        return None

    def remove_direction(self, direction):
        for direction_index in range(self.directions):
            if self.directions[direction_index] is direction:
                self.directions.pop(direction_index)
                self.size -= 1
                """
                self.available_states = self.create_states()  # tuple[tuple[Lane]]
                self.states_size = len(self.available_states)
                """

    def get_traffic_lights(self):
        res = set()
        groups = set()

        for direction in self.directions:
            lanes_group = set()
            directions_group = set()
            for lane in direction.in_lanes:
                if 0 == len(directions_group):
                    lanes_group.add(lane)
                    directions_group.update(to_lane.parent_direction for to_lane in lane.to_lanes)
                else:
                    directions_check_group = set()
                    directions_check_group.update(to_lane.parent_direction for to_lane in lane.to_lanes)
                    if not (directions_check_group & directions_group):  # if the intersection of the sets is empty
                        groups.add(frozenset(lanes_group))
                        lanes_group.clear()
                        lanes_group.add(lane)
                        directions_group = directions_check_group
                    else:
                        lanes_group.add(lane)
                        directions_group = directions_check_group | directions_group  # updates the group to be the union of both of them
            groups.add(frozenset(lanes_group))

        for lanes_group_index in range(len(groups)):
            tl = TrafficLight(str(lanes_group_index), list(list(groups)[lanes_group_index]))
            res.add(tl)

        self.traffic_lights = res
        return res

    def create_states(self):
        states = set()
        if not self.size >= 2:
            return None

        traffic_lights = list(self.get_traffic_lights())

        """
        for direction in self.directions:
            state = []
            for traffic_light in traffic_lights:
                if traffic_light.get_direction() is direction:
                    state.append(traffic_light)
            states.add(tuple(state))
        """
        
        for traffic_light in traffic_lights:
            reward, state = solve_custom_knapsack(traffic_lights, traffic_light, self.size, self)
        states.add(tuple(set(state)))

        return tuple(states)


    def set_directions_module_indexes(self, main_direction):
        module_index = 0
        for index in range(self.size):
            self.directions[index].module_index = index
            if main_direction is self.directions[index]:
                module_index = index

        for index in range(self.size):
            self.directions[index].module_index = (self.directions[index].module_index - module_index) % self.size

    def set_states(self):
        self.available_states = self.create_states()
        self.states_size = len(self.available_states)

    def set_traffic_lights_states(self, active_index):
        self.active_index = active_index
        self.active_state = self.available_states[active_index]

        for traffic_light in self.traffic_lights:
            traffic_light.set_state(State.RED)

        for traffic_light in self.active_state:
            traffic_light.set_state(State.GREEN)

    def update_state(self):
        common_traffic_lights = set()
        next_active_index = (self.active_index + 1) % self.states_size
        next_active_state = self.available_states[self.active_index]

        for traffic_light in self.active_state:
            if traffic_light in next_active_state:
                common_traffic_lights.add(traffic_light)

        # start updating

        for traffic_light in self.active_state:
            if traffic_light not in common_traffic_lights:
                traffic_light.update_state()  # to GREEN_FLICKERING

        time.sleep(3)

        for traffic_light in self.active_state:
            if traffic_light not in common_traffic_lights:
                traffic_light.update_state()  # to YELLOW

        time.sleep(2)

        for traffic_light in self.active_state:
            if traffic_light not in common_traffic_lights:
                traffic_light.update_state()  # active_state lanes to RED

        self.active_index = next_active_index
        self.active_state = next_active_state

        for traffic_light in self.active_state:
            if traffic_light not in common_traffic_lights:
                traffic_light.update_state()  # active_state lanes to RED_YELLOW

        time.sleep(2)

        for traffic_light in self.active_state:
            if traffic_light not in common_traffic_lights:
                traffic_light.update_state()  # active_state lanes to GREEN

    def __str__(self):
        res = f"Junction has {self.size} directions:\n\n"
        for direction in self.directions:
            res += f"\t{direction}\n"
        return res
