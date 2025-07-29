"""
Utility Functions Module

This module contains utility functions used throughout the traffic simulation system
for collision detection, object searching, filtering, and traffic light optimization.
These functions provide essential algorithms for the simulation's core functionality.

Functions:
    are_there_possible_collisions: Detects potential collisions between lanes
    find_obj_index_in_array: Finds the index of an object in an array
    filter_greater_than_or_equal_to: Filters values greater than or equal to threshold
    filter_less_than: Filters values less than threshold
    get_blocked_traffic_lights_by_traffic_light: Finds traffic lights blocked by another
    get_blocked_traffic_lights_by_traffic_lights: Finds traffic lights blocked by a set
    solve_custom_knapsack: Solves a custom knapsack problem for traffic light optimization
    sort_and_remove_duplicates_in_tuple: Sorts and removes duplicates from a tuple
    sort_tuple: Sorts a tuple
    remove_duplicates_in_tuple: Removes duplicates from a sorted tuple
"""

def are_there_possible_collisions(lanes):
    """
    Checks if there are possible collisions between the given in-lanes.
    A collision can occur when two in-lanes have overlapping paths to their respective out-lanes.
    
    Args:
        lanes (list[Lane]): List of in-lanes to check for collisions
        
    Returns:
        bool: True if there are possible collisions, False otherwise
        
    Note:
        This function analyzes the paths that vehicles would take from in-lanes to out-lanes
        and detects potential conflicts. It considers both same-direction and cross-direction
        conflicts, taking into account the relative positions of lanes within directions.
    """
    if not lanes:
        return False
        
    # For each pair of lanes, check if their paths could intersect
    for i in range(len(lanes)):
        lane1 = lanes[i]
        if not lane1.to_lanes:  # Skip if lane has no destinations
            continue
            
        for j in range(i + 1, len(lanes)):
            lane2 = lanes[j]
            if not lane2.to_lanes:  # Skip if lane has no destinations
                continue
                
            # Get the sets of out-lanes that each in-lane can reach
            lane1_out_lanes = set(lane1.to_lanes)
            lane2_out_lanes = set(lane2.to_lanes)
            
            # If there's any overlap in the out-lanes, there's a potential collision
            if lane1_out_lanes & lane2_out_lanes:
                # Check if the lanes are from the same direction
                if lane1.parent_direction == lane2.parent_direction:
                    # If they're from the same direction, check their relative positions
                    # Lanes are ordered from right to left in a direction
                    lane1_index = lane1.parent_direction.in_lanes.index(lane1)
                    lane2_index = lane2.parent_direction.in_lanes.index(lane2)
                    
                    # If lane1 is to the right of lane2, their paths shouldn't cross
                    # This is because vehicles should maintain their relative positions
                    if lane1_index < lane2_index:
                        # Check if lane1's rightmost out-lane is to the right of lane2's leftmost out-lane
                        lane1_rightmost = min(lane1.parent_direction.out_lanes.index(out) for out in lane1.to_lanes)
                        lane2_leftmost = max(lane2.parent_direction.out_lanes.index(out) for out in lane2.to_lanes)
                        if lane1_rightmost > lane2_leftmost:
                            return True
                else:
                    # If they're from different directions, any overlap in out-lanes is a collision
                    return True
                    
    return False


def find_obj_index_in_array(obj, arr):
    """
    Find the index of an object in an array.
    
    Args:
        obj: The object to search for
        arr: The array to search in
        
    Returns:
        int or None: The index of the object if found, None otherwise
    """
    if None is arr:
        return None
    i = 0
    for element in arr:
        if element is obj:
            return i
        i += 1
    return None


def filter_greater_than_or_equal_to(tup, threshold, default_val):
    """
    Filter values in a tuple that are greater than or equal to a threshold.
    
    Args:
        tup (tuple): The tuple to filter
        threshold: The threshold value to compare against
        default_val: Default value to include in the result
        
    Returns:
        tuple: Filtered tuple containing values >= threshold plus default value
    """
    res = [default_val]
    for x in tup:
        if x >= threshold:
            res.append(x)
    return tuple(res)


def filter_less_than(tup, threshold, default_val):
    """
    Filter values in a tuple that are less than a threshold.
    
    Args:
        tup (tuple): The tuple to filter
        threshold: The threshold value to compare against
        default_val: Default value to include in the result
        
    Returns:
        tuple: Filtered tuple containing values < threshold plus default value
    """
    res = [default_val]
    for x in tup:
        if x < threshold:
            res.append(x)
    return tuple(res)


def get_blocked_traffic_lights_by_traffic_light(junction, blocking_traffic_light):
    """
    Find traffic lights that would be blocked by a specific traffic light.
    
    This function determines which traffic lights would conflict with the given
    traffic light based on their directions and potential path intersections.
    
    Args:
        junction (Junction): The junction containing the traffic lights
        blocking_traffic_light (TrafficLight): The traffic light that would block others
        
    Returns:
        set: Set of TrafficLight objects that would be blocked
    """
    blocked_traffic_lights = set()

    main_direction = blocking_traffic_light.get_direction()
    junction.set_directions_module_indexes(main_direction)
    directions_directing_indexes = blocking_traffic_light.get_directions_directing_indexes()

    for traffic_light in junction.traffic_lights:
        if traffic_light is blocking_traffic_light:
            continue
        elif main_direction is traffic_light.get_direction():
            continue

        traffic_light_is_valid = True

        target_direction_module_index = traffic_light.get_direction().module_index
        max_direction_index = min(filter_greater_than_or_equal_to(directions_directing_indexes, target_direction_module_index,junction.size - 1))
        min_direction_index = max(filter_less_than(directions_directing_indexes, target_direction_module_index, 0))

        for lane in traffic_light.lanes:
            for to_lane in lane.to_lanes:
                to_lane_direction_index = to_lane.parent_direction.module_index
                if min_direction_index < to_lane_direction_index < max_direction_index:
                    continue
                elif min_direction_index == to_lane_direction_index:
                    if not (blocking_traffic_light.get_minimum_to_lane_index_by_direction(to_lane.parent_direction) > to_lane.index_in_junction):
                        traffic_light_is_valid = False
                elif max_direction_index == to_lane_direction_index:
                    if not (blocking_traffic_light.get_maximum_to_lane_index_by_direction(to_lane.parent_direction) < to_lane.index_in_junction):
                        traffic_light_is_valid = False
                else:
                    traffic_light_is_valid = False

        if not traffic_light_is_valid:
            blocked_traffic_lights.add(traffic_light)
    return blocked_traffic_lights


def get_blocked_traffic_lights_by_traffic_lights(junction, blocking_traffic_lights):
    """
    Find all traffic lights that would be blocked by a set of blocking traffic lights.
    
    This function aggregates the results of get_blocked_traffic_lights_by_traffic_light
    for each traffic light in the blocking set.
    
    Args:
        junction (Junction): The junction containing the traffic lights
        blocking_traffic_lights (iterable): Iterable of TrafficLight objects to check as blockers
    
    Returns:
        set: Set of TrafficLight objects that would be blocked by any in the blocking set
    """
    blocked_traffic_lights = set()
    for blocking_traffic_light in blocking_traffic_lights:
        blocked_traffic_lights = blocked_traffic_lights | get_blocked_traffic_lights_by_traffic_light(junction, blocking_traffic_light)
    return blocked_traffic_lights


def solve_custom_knapsack(items, must_include, capacity: int, junction):
    """
    Solve a custom knapsack problem for traffic light optimization.
    
    This function selects a combination of items (traffic lights) to maximize reward
    (total size), subject to a capacity constraint, and must include a specific item.
    Uses backtracking to explore all valid combinations.
    
    Args:
        items (list): List of items (traffic lights) to consider
        must_include: The item that must be included in the solution
        capacity (int): Maximum allowed total weight
        junction: The junction context for weight calculations
    
    Returns:
        tuple: (best_reward, best_combination) where best_reward is the maximum reward
               and best_combination is the list of selected items
    """
    best_reward = must_include.size
    best_combination = [must_include]

    def backtrack(index: int, included, total_reward: int, total_weight: int):
        nonlocal best_reward, best_combination

        # Base case: reached end of items list
        if index == len(items):
            # Check if solution is valid (includes required item and within capacity)
            if must_include in included and total_weight <= capacity:
                # Update the best solution if current is better
                if total_reward > best_reward:
                    best_reward = total_reward
                    best_combination = list(included)
            return

        item = items[index]

        # Handle the must_include item specially
        if item is must_include:
            # Skip including must_include again since it's already in the solution
            backtrack(index + 1, included, total_reward, total_weight)
        else:
            # Try including this item
            next_included = included | {item}
            weight = item.get_weight(included, junction)
            if total_weight + weight <= capacity:
                # Recursively explore with this item included
                backtrack(index + 1, next_included, total_reward + item.size, total_weight + weight)

            # Try excluding this item (always possible)
            backtrack(index + 1, included, total_reward, total_weight)

    # Start recursion
    init_included = set()
    init_included.add(must_include)
    backtrack(0, init_included, best_reward, must_include.get_weight(set(), junction))
    return best_reward, best_combination


def sort_and_remove_duplicates_in_tuple(tup):
    """
    Sort a tuple and remove duplicate elements.
    
    Args:
        tup (tuple): The tuple to sort and deduplicate
    
    Returns:
        tuple: Sorted tuple with duplicates removed
    
    Raises:
        TypeError: If input is not a tuple
    """
    if not isinstance(tup, tuple):
        raise TypeError("tup is invalid: Not a tuple")
    return remove_duplicates_in_tuple(sort_tuple(tup))


def sort_tuple(tup):
    """
    Sort the elements of a tuple.
    
    Args:
        tup (tuple): The tuple to sort
    
    Returns:
        tuple: Sorted tuple
    
    Raises:
        TypeError: If input is not a tuple
    """
    if not isinstance(tup, tuple):
        raise TypeError("tup is invalid: Not a tuple")
    return tuple(sorted(tup))


def remove_duplicates_in_tuple(tup):
    """
    Remove duplicate elements from a sorted tuple.
    
    Args:
        tup (tuple): Sorted tuple from which to remove duplicates
    
    Returns:
        tuple: Tuple with duplicates removed
    
    Raises:
        TypeError: If input is not a tuple
    """
    if not isinstance(tup, tuple):
        raise TypeError("tup is invalid: Not a tuple")
    size = len(tup)
    if size < 2:
        return tup

    lst = list(tup)
    i = 0
    condition = True
    while condition:
        if lst[i] == lst[i+1]:
            lst.pop(i+1)
            size -= 1
        else:
            i += 1
        condition = i < size - 1
    return tuple(lst)
