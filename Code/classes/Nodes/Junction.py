"""
Junction Module

This module contains the Junction class and related functions for managing traffic
junctions in the simulation system. A Junction represents a traffic intersection
with multiple directions, traffic lights, and complex traffic control algorithms.

Classes:
    Junction: Represents a traffic junction with directions and traffic control.

Functions:
    check_junction_validity: Validates a list of directions for junction creation.
    is_vehicle_relevant: Determines if a vehicle is relevant for traffic control decisions.
    get_filter_value: Calculates filter values for traffic light optimization.
    get_score_value: Calculates score values for traffic light state selection.
"""

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
    
    Args:
        directions (list of Direction): The list of directions to validate
        
    Returns:
        bool: True if all directions are valid for junction creation
        
    Raises:
        TypeError: If the directions list is invalid or contains non-Direction objects
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

"""
# TODO: delete later - debug use
import threading

counter_test_amount = 0
counter_flag1 = 0
counter_flag2 = 0
counter_flag3 = 0
# Create a mutex lock
lock = threading.Lock()
"""

# TODO: delete later - debug use
import threading

counter_greenwave = 0
counter_adaptive = 0
# Create a mutex lock
lock = threading.Lock()

def is_vehicle_relevant(vehicle, start_seconds, end_seconds, lane, is_now_green, is_to_green):
    """
    Determine if a vehicle is relevant for traffic control decisions.
    
    Args:
        vehicle (Vehicle): The vehicle to check
        start_seconds (int): Start time in seconds for the time range
        end_seconds (int): End time in seconds for the time range
        lane (Lane): The lane the vehicle is on
        is_now_green (bool): Whether the traffic light is currently green
        is_to_green (bool): Whether the traffic light will turn green
        
    Returns:
        bool: True if the vehicle is relevant for traffic control decisions
        
    Note:
        This function determines vehicle relevance based on arrival time,
        whether it's the final lane, and traffic light state transitions.
    """
    # TODO: return the function to it's normal state

    # global counter_test_amount, counter_flag1, counter_flag2, counter_flag3, lock

    result = True
    
    # Check if vehicle will arrive within the specified time window
    result = result and vehicle.is_away_from_next_junction_by_between_start_and_end_seconds(start_seconds, end_seconds)
    # Exclude vehicles that are on their final destination lane
    result = result and not vehicle.is_next_lane_the_final_lane()
    # if is_to_green and result:
    #     result = result and not lane.will_be_there_queue_in_given_seconds_for_to_green(vehicle.get_time_to_next_junction_in_sec(), is_now_green)

    """
    flag1 = vehicle.is_away_from_next_junction_by_between_start_and_end_seconds(start_seconds, end_seconds)
    flag2 = not vehicle.is_next_lane_the_final_lane()
    # flag3 = not lane.will_stop_or_pass_anyway_in_given_seconds(seconds_to_junction, is_now_green)

    seconds_to_junction = vehicle.get_time_to_next_junction_in_sec()

    condition = seconds_to_junction <= 13 and ((is_now_green and seconds_to_junction >= 3) or (not is_now_green and seconds_to_junction >= 7))

    if condition:
        flag3 = not lane.will_pass_anyway_in_given_seconds(seconds_to_junction, is_now_green)

    result = flag1 and flag2 and flag3

    with lock:
        counter_test_amount += 1
        counter_flag1 += 1 if flag1 else 0
        counter_flag2 += 1 if flag2 else 0
        counter_flag3 += 1 if flag3 else 0
        print(f"GGGGGGGGGGGGGGG, counter_test_amount = {counter_test_amount}, counter_flag1 = {counter_flag1}, counter_flag2 = {counter_flag2}, counter_flag3 = {counter_flag3}, result = {result}")
    """

    return result

def get_filter_value(filter, traffic_lights, is_to_green, is_to_stay, same_state_check_flag, seconds=None):
    """
    Calculate filter values for traffic light optimization.
    
    Args:
        filter (str): The filter type ("energy" or "pollution")
        traffic_lights (list): List of traffic lights to evaluate
        is_to_green (bool): Whether traffic lights will turn green
        is_to_stay (bool): Whether traffic lights will stay in current state
        same_state_check_flag (bool): Flag for same state checking
        seconds (int, optional): Time in seconds for evaluation
        
    Returns:
        float: The calculated filter value
    """
    value = 0

    filter_changed = False
    filter_value = 0

    # Dynamic time window: shorter for state changes, longer for staying
    start_seconds = 3 if (is_to_green and is_to_stay) or (not is_to_green and not is_to_stay) else 7
    end_seconds = 17  # 13 if is_to_green else 17

    if same_state_check_flag:
        start_seconds = 3
        end_seconds = seconds

    for traffic_light in traffic_lights:
        for lane in traffic_light.lanes:
            vehicles = lane.road_lane.vehicles
            for vehicle in vehicles:
                if is_vehicle_relevant(vehicle, start_seconds, end_seconds, lane, is_now_green):
                    # Calculate target velocity considering road and vehicle limits
                    to_velocity = min(vehicle.roads_path[vehicle.roads_passed][0].road_lane.parent_road.maximum_speed, vehicle.maximum_speed)
                    match filter:
                        case "energy":
                            value = vehicle.get_energy_consumption_to_velocity(to_velocity)
                        case "pollution":
                            value = vehicle.get_pollution_to_velocity(to_velocity)

                    # Determine if vehicle will stop or pass based on traffic light state
                    will_stop, will_pass = lane.will_stop_or_pass_due_to_state_in_given_seconds(vehicle.get_time_to_next_junction_in_sec(), is_to_green, is_to_stay)
                    # Subtract energy/pollution if vehicle can pass without stopping (green wave benefit)
                    if (is_to_green or will_pass) and (not will_stop):
                        filter_value -= value
                    filter_changed = True

    return filter_value, filter_changed


def get_score_value(filter, traffic_lights, is_now_green, is_to_green, same_state_check_flag=None, seconds=None):
    value = 0

    value_changed = False
    filter_value = 0

    # Time window based on current traffic light state
    start_seconds = 3 if is_now_green else 7
    end_seconds = 17  # 13 if is_to_green else 17

    if same_state_check_flag:
        start_seconds = 3
        end_seconds = seconds

    for traffic_light in traffic_lights:
        for lane in traffic_light.lanes:
            vehicles = lane.road_lane.vehicles
            for vehicle in vehicles:
                if is_vehicle_relevant(vehicle, start_seconds, end_seconds, lane, is_now_green, is_to_green):
                    # Calculate target velocity considering road and vehicle limits
                    to_velocity = min(vehicle.roads_path[vehicle.roads_passed][0].road_lane.parent_road.maximum_speed, vehicle.maximum_speed)
                    match filter:
                        case "energy":
                            value = vehicle.get_energy_consumption_to_velocity(to_velocity)
                        case "pollution":
                            value = vehicle.get_pollution_to_velocity(to_velocity)

                    # will_stop, will_pass = lane.will_stop_or_pass_due_to_state_in_given_seconds(vehicle.get_time_to_next_junction_in_sec(), is_now_green, is_to_green)
                    # if will_stop:
                    #     filter_value += value
                    # elif is_to_green or will_pass:
                    #     filter_value -= value
                    # else:
                    #     filter_value += value

                    value = -1 * value if is_to_green else value
                    # value = 0 if is_to_green else value
                    filter_value += value
                    value_changed = True

    return filter_value, value_changed


class Junction:
    """
    Represents a traffic junction with multiple directions and traffic control systems.
    
    A Junction manages multiple directions, traffic lights, and implements various
    traffic control algorithms including fixed timing, adaptive control, and green
    wave optimization for energy and pollution reduction.
    
    The junction is assumed to be circular, meaning direction[0] is adjacent to
    both direction[n-1] and direction[1], and direction[k] is adjacent to both
    direction[k-1] and direction[k+1]. Directions are sorted counter-clockwise.
    
    Attributes:
        directions (list): List of Direction objects in the junction
        size (int): Number of directions in the junction
        traffic_lights (list): List of TrafficLight objects
        available_states (list): List of available traffic light states
        states_size (int): Number of available states
        active_state (int): Currently active state index
        active_index (int): Index of active state in available_states
        point (Point): Geographical position of the junction
        junction_index (int): Unique index of this junction
        distance (float): Distance for BFS algorithms
        source_junction (Junction): Source junction for BFS algorithms
        prevent_state_change (bool): Flag to prevent state changes
    """

    def __init__(self, directions=None):  # directions: list[Direction]
        """
        Initialize a new Junction instance.
        
        Args:
            directions (list of Direction, optional): List of directions for this junction
        """
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
        # Calculate which traffic lights need to change state
        traffic_lights_to_turn_red = tuple(set(self.active_state) - set(next_active_state))
        traffic_lights_to_turn_green = tuple(set(next_active_state) - set(self.active_state))

        # start updating

        # Phase 1: Turn traffic lights to green flickering (warning)
        for traffic_light in traffic_lights_to_turn_red:
            traffic_light.update_state()  # to GREEN_FLICKERING

        time.sleep(3)  # Wait for drivers to notice the warning

        # Phase 2: Turn traffic lights to yellow (prepare to stop)
        for traffic_light in traffic_lights_to_turn_red:
            traffic_light.update_state()  # to YELLOW

        time.sleep(2)  # Give time for vehicles to stop

        # Phase 3: Turn traffic lights to red (stop traffic)
        for traffic_light in traffic_lights_to_turn_red:
            traffic_light.update_state()  # active_state lanes to RED

        self.active_index = next_active_index
        self.active_state = next_active_state

        # Phase 4: Turn new traffic lights to red-yellow (prepare to go)
        for traffic_light in traffic_lights_to_turn_green:
            traffic_light.update_state()  # active_state lanes to RED_YELLOW

        time.sleep(2)  # Wait before turning green

        # Phase 5: Turn traffic lights to green (start traffic)
        for traffic_light in traffic_lights_to_turn_green:
            traffic_light.update_state()  # active_state lanes to GREEN

        # Start a thread to wait before allowing next state change
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





    def calculate_green_wave_switch_score(self, filter, next_active_index, seconds=None):
        score_changed = False
        score_value = 0

        next_active_state = self.available_states[next_active_index]

        # Categorize traffic lights based on current and future states
        traffic_lights_currently_red = set(self.traffic_lights) - set(self.active_state)
        traffic_lights_currently_green = set(self.active_state)
        traffic_lights_will_be_red = set(self.traffic_lights) - set(next_active_state)
        traffic_lights_will_be_green = set(next_active_state)

        # Group traffic lights by their state transition type
        traffic_lights_to_turn_red = tuple(traffic_lights_currently_green.intersection(traffic_lights_will_be_red))  # only vehicles which are left with 3 seconds could cross without stopping
        traffic_lights_to_turn_green = tuple(traffic_lights_currently_red.intersection(traffic_lights_will_be_green))  # only vehicles which are left with 7 to 10 seconds could cross without stopping
        traffic_lights_to_stay_red = tuple(traffic_lights_currently_red.intersection(traffic_lights_will_be_red))  # all vehicles will come to stop up to at least 10 seconds
        traffic_lights_to_stay_green = tuple(traffic_lights_currently_green.intersection(traffic_lights_will_be_green))

        # traffic_lights_group = ((traffic_lights_to_stay_red, False, False), (traffic_lights_to_turn_red, True, False), (traffic_lights_to_stay_green, True, True), (traffic_lights_to_turn_green, False, True))
        traffic_lights_group = ((traffic_lights_to_stay_green, True, True), (traffic_lights_to_turn_green, False, True))

        # Calculate score for each group of traffic lights
        for traffic_lights, is_now_green, is_to_green in traffic_lights_group:
            val, flag = get_score_value(filter, traffic_lights, is_now_green=is_now_green, is_to_green=is_to_green, same_state_check_flag=self.active_index == next_active_index, seconds=seconds)
            score_value += val
            score_changed = score_changed or flag

        return score_value, score_changed

    def green_wave_adaptive(self):
        max_amount, score_index, score_changed = 0, self.active_index, False

        for state_index in range(self.states_size):
            state = self.available_states[state_index]
            score = 0

            for traffic_light in state:
                for lane in traffic_light.lanes:
                    # Count vehicles that will arrive within the green wave window (3-17 seconds)
                    score += len(lane.road_lane.get_list_of_vehicles_which_are_left_with_more_than_one_junction_sorted_by_arrival_time_from_and_to_seconds(3, 17))
                    # score += 0.1 * len(lane.vehicles_queue)

            # Select state with maximum number of vehicles in green wave window
            if max_amount < score:
                max_amount = score
                score_index = state_index
                score_changed = True

        if score_changed:
            return score_index
        # Fallback to simple vehicle count if no green wave opportunity found
        return self.get_max_vehicle_count_state_index()


    def get_green_wave_state_index(self, filter):
        global counter_greenwave, counter_adaptive, lock

        min_score, score_index, score_changed = float("inf"), None, False

        # First, evaluate all other states to find the best switch
        for state_index in range(self.states_size):
            if state_index != self.active_index:
                score, changed_flag = self.calculate_green_wave_switch_score(filter, state_index)
                if min_score > score and changed_flag:
                    min_score = score
                    score_index = state_index
                    score_changed = True

        # Then, evaluate staying in current state with different timing windows (4-17 seconds)
        for seconds in range(4, 18):
            score, changed_flag = self.calculate_green_wave_switch_score(filter, self.active_index, seconds)
            if min_score > score and changed_flag:
                min_score = score
                score_index = self.active_index
                score_changed = True

        if score_changed:
            # Use green wave optimization
            with lock:
                counter_greenwave += 1
            print(f"DEBUG GREEN WAVE, counter_greenwave = {counter_greenwave}, counter_adaptive = {counter_adaptive}")
            return score_index
        # Fallback to adaptive algorithm if no green wave opportunity
        with lock:
            counter_adaptive += 1
        print(f"DEBUG ADAPTIVE, counter_greenwave = {counter_greenwave}, counter_adaptive = {counter_adaptive}")
        return self.green_wave_adaptive()







    """
    def get_green_wave_state_index(self):
        max_vehicle_count = 0
        res_index = self.active_index
        res_index_changed = False

        for state_index in range(self.states_size):
            temp_vehicle_count = 0
            next_active_state = self.available_states[state_index]
            traffic_lights_to_stay_green = tuple(set(self.active_state).intersection(set(next_active_state)))

            for traffic_light in next_active_state:
                for lane in traffic_light.lanes:
                    start_seconds = 3 if traffic_light in traffic_lights_to_stay_green else 7
                    temp_vehicle_count += len(lane.road_lane.get_list_of_vehicles_which_are_left_with_more_than_one_junction_sorted_by_arrival_time_from_and_to_seconds(start_seconds, 13))
                    #print(f"temp_vehicle_count = {temp_vehicle_count} and max_vehicle_count = {max_vehicle_count}")
            if temp_vehicle_count > max_vehicle_count:
                max_vehicle_count = temp_vehicle_count
                res_index = state_index
                res_index_changed = True

        if res_index_changed:
            return res_index
        return self.get_max_vehicle_count_state_index()
    """

    def get_max_vehicle_count_state_index_in_road_lane(self):
        max_vehicle_count = 0
        res_index = self.active_index
        res_index_changed = False

        for state_index in range(self.states_size):
            temp_vehicle_count = 0
            next_active_state = self.available_states[state_index]
            for traffic_light in next_active_state:
                # traffic_lights_to_turn_green = tuple(set(next_active_state) - set(self.active_state))  # only vehicles which are left with 7 to 10 seconds could cross without stopping
                traffic_lights_to_stay_green = tuple(set(self.active_state).intersection(set(next_active_state)))  # all vehicles will cross without stopping

                for lane in traffic_light.lanes:
                    vehicles = lane.road_lane.vehicles
                    start_seconds = 3 if traffic_light in traffic_lights_to_stay_green else 7
                    for vehicle in vehicles:
                        if is_vehicle_relevant(vehicle, start_seconds, 13, lane, is_now_green):
                            temp_vehicle_count += 1

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

        # Get traffic lights that are currently red
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
            # Focus on traffic lights that will stay green or turn green (positive impact)
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
