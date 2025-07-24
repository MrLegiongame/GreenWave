import time
from typing import Set, List
import threading

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

def is_vehicle_relevant(vehicle, start_seconds, end_seconds, lane):
    result = True
    result = result and vehicle.is_away_from_next_junction_by_between_start_and_end_seconds(start_seconds, end_seconds)
    result = result and not vehicle.is_next_lane_the_final_lane()
    result = result and not lane.will_stop_or_pass_anyway_in_given_seconds(vehicle.get_time_to_next_junction_in_sec())

    return result

def get_filter_value(filter, traffic_lights, is_to_green, is_to_stay, same_state_check_flag, seconds=None):
    value = 0

    filter_changed = False
    filter_value = 0

    start_seconds = 3 if (is_to_green and is_to_stay) or (not is_to_green and not is_to_stay) else 7
    end_seconds = 13 if is_to_green else 17

    if same_state_check_flag:
        start_seconds = 3
        end_seconds = seconds

    for traffic_light in traffic_lights:
        for lane in traffic_light.lanes:
            vehicles = lane.road_lane.vehicles
            for vehicle in vehicles:
                if is_vehicle_relevant(vehicle, start_seconds, end_seconds, lane):
                    to_velocity = min(vehicle.roads_path[vehicle.roads_passed][0].road_lane.parent_road.maximum_speed, vehicle.maximum_speed)
                    match filter:
                        case "energy":
                            value = vehicle.get_energy_consumption_to_velocity(to_velocity)
                        case "pollution":
                            value = vehicle.get_pollution_to_velocity(to_velocity)

                    will_stop, will_pass = lane.will_stop_or_pass_due_to_state_in_given_seconds(vehicle.get_time_to_next_junction_in_sec(), is_to_green, is_to_stay)
                    if (is_to_green or will_pass) and (not will_stop):
                        filter_value -= value
                    filter_changed = True

    return filter_value, filter_changed


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
        self.prevent_state_change = False

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

    def wait(self, seconds):
        time.sleep(seconds)
        self.prevent_state_change = False

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

    def update_state(self, next_active_index):
        if next_active_index == self.active_index:
            self.prevent_state_change = False
            return

        next_active_state = self.available_states[next_active_index]
        traffic_lights_to_turn_red = tuple(set(self.active_state) - set(next_active_state))
        traffic_lights_to_turn_green = tuple(set(next_active_state) - set(self.active_state))

        # start updating

        for traffic_light in traffic_lights_to_turn_red:
            traffic_light.update_state()  # to GREEN_FLICKERING

        time.sleep(3)

        for traffic_light in traffic_lights_to_turn_red:
            traffic_light.update_state()  # to YELLOW

        time.sleep(2)

        for traffic_light in traffic_lights_to_turn_red:
            traffic_light.update_state()  # active_state lanes to RED

        self.active_index = next_active_index
        self.active_state = next_active_state

        for traffic_light in traffic_lights_to_turn_green:
            traffic_light.update_state()  # active_state lanes to RED_YELLOW

        time.sleep(2)

        for traffic_light in traffic_lights_to_turn_green:
            traffic_light.update_state()  # active_state lanes to GREEN

        threading.Thread(target=self.wait, args=(3,)).start()

    def get_max_weighted_state_index(self):
        max_weight = 0
        res_index = self.active_index
        for state_index in range(self.states_size):
            temp_weight = 0
            for traffic_light in self.available_states[state_index]:
                for lane in traffic_light.lanes:
                    for vehicle in lane.vehicles_queue:
                        temp_weight += vehicle.weight
            if temp_weight > max_weight:
                max_weight = temp_weight
                res_index = state_index
        return res_index

    def get_max_vehicle_count_state_index(self):
        max_vehicle_count = 0
        res_index = self.active_index
        for state_index in range(self.states_size):
            temp_vehicle_count = 0
            for traffic_light in self.available_states[state_index]:
                for lane in traffic_light.lanes:
                    temp_vehicle_count += len(lane.vehicles_queue)
            if temp_vehicle_count > max_vehicle_count:
                max_vehicle_count = temp_vehicle_count
                res_index = state_index
        return res_index

    def get_max_vehicle_count_state_index_in_road_lane(self):
        max_vehicle_count = 0
        res_index = self.active_index
        res_index_changed = False

        for state_index in range(self.states_size):
            temp_vehicle_count = 0
            for traffic_light in self.available_states[state_index]:
                for lane in traffic_light.lanes:

                    """
                    vehicles = lane.road_lane.vehicles
                    if traffic_light in self.active_state:
                        start_seconds = 3
                    else:
                        start_seconds = 7
                    for vehicle in vehicles:
                        if is_vehicle_relevant(vehicle, start_seconds, 13, lane):
                            temp_vehicle_count += 1
                    """

                    if traffic_light in self.active_state:
                        temp_vehicle_count += len(lane.road_lane.get_list_of_vehicles_which_are_left_with_more_than_one_junction_sorted_by_arrival_time_from_and_to_seconds(3, 13))
                    else:
                        temp_vehicle_count += len(lane.road_lane.get_list_of_vehicles_which_are_left_with_more_than_one_junction_sorted_by_arrival_time_from_and_to_seconds(7, 13))
            if temp_vehicle_count > max_vehicle_count:
                max_vehicle_count = temp_vehicle_count
                res_index = state_index
                res_index_changed = True

        if res_index_changed:
            return res_index
        return self.get_max_vehicle_count_state_index()

    def get_min_expected_filter_state_index(self, filter):
        min_filter_value = float("inf")
        res_index = self.active_index
        res_index_changed = False

        traffic_lights_which_are_currently_red = tuple(set(self.traffic_lights) - set(self.active_state))

        for next_active_index in range(self.states_size):
            temp_filter_changed = False
            temp_filter_value = 0

            # Creates relevant traffic lights groups
            next_active_state = self.available_states[next_active_index]
            traffic_lights_to_turn_red = tuple(set(self.active_state) - set(next_active_state))  # only vehicles which are left with 3 seconds could cross without stopping
            traffic_lights_to_turn_green = tuple(set(next_active_state) - set(self.active_state))  # only vehicles which are left with 7 to 10 seconds could cross without stopping
            traffic_lights_to_stay_red = tuple(set(traffic_lights_which_are_currently_red) - set(traffic_lights_to_turn_green))  # all vehicles will come to stop up to at least 10 seconds
            traffic_lights_to_stay_green = tuple(set(self.active_state).intersection(set(next_active_state)))  # all vehicles will cross without stopping

            # traffic_lights_group = ((traffic_lights_to_stay_red, False, True), (traffic_lights_to_turn_red, False, False), (traffic_lights_to_stay_green, True, True), (traffic_lights_to_turn_green, True, False))
            traffic_lights_group = ((traffic_lights_to_stay_green, True, True), (traffic_lights_to_turn_green, True, False))
            for traffic_lights, is_to_green, is_to_stay in traffic_lights_group:
                val, flag = get_filter_value(filter, traffic_lights, is_to_green=is_to_green, is_to_stay=is_to_stay, same_state_check_flag=False)  # we want to focus on the vehicles coming between 7 and 13 seconds, all other vehicles will stop ANYWAY
                temp_filter_value += val
                temp_filter_changed = temp_filter_changed or flag

            # print(f"DEBUG PARAMETERS: next_active_index = {next_active_index}, junction_index_in_map = {self.junction_index}, temp_filter_value = {temp_filter_value}, temp_filter_changed = {temp_filter_changed}")  # TODO: delete later- for debug use
            if temp_filter_changed:
                print(f"DEBUG temp_filter_value = {temp_filter_value}, min_filter_value = {min_filter_value}")
            if temp_filter_value < min_filter_value and temp_filter_changed:
                min_filter_value = temp_filter_value
                res_index = next_active_index
                res_index_changed = True

        """
        for seconds in range(4, 17):
            temp_filter_changed = False
            temp_filter_value = 0

            # Creates relevant traffic lights group
            traffic_lights_to_stay_green = self.active_state  # all vehicles will cross without stopping

            # traffic_lights_group = (traffic_lights_to_stay_red, False, True), (traffic_lights_to_stay_green, True, True)
            traffic_lights_group = ((traffic_lights_to_stay_green, True, True), )
            for traffic_lights, is_to_green, is_to_stay in traffic_lights_group:
                val, flag = get_filter_value(filter, traffic_lights, is_to_green=is_to_green, is_to_stay=is_to_stay, same_state_check_flag=True, seconds=seconds)  # we want to focus on the vehicles coming between 7 and 13 seconds, all other vehicles will stop ANYWAY
                temp_filter_value += val
                temp_filter_changed = temp_filter_changed or flag

            if temp_filter_value < min_filter_value and temp_filter_changed:
                min_filter_value = temp_filter_value
                res_index = self.active_index
                res_index_changed = True
        """

        if res_index_changed:
            return res_index

        return self.get_max_vehicle_count_state_index_in_road_lane()

    def __str__(self):
        res = f"Junction has {self.size} directions:\n\n"
        for direction in self.directions:
            res += f"\t{direction}\n"
        return res
