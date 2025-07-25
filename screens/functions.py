def are_there_possible_collisions(lanes):
    """
    Checks if there are possible collisions between the given in-lanes.
    A collision can occur when two in-lanes have overlapping paths to their respective out-lanes.
    
    Args:
        lanes: list[Lane] - List of in-lanes to check for collisions
        
    Returns:
        bool: True if there are possible collisions, False otherwise
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
    if None is arr:
        return None
    i = 0
    for element in arr:
        if element is obj:
            return i
        i += 1
    return None


def filter_greater_than_or_equal_to(tup, threshold, default_val):
    res = [default_val]
    for x in tup:
        if x >= threshold:
            res.append(x)
    return tuple(res)


def filter_less_than(tup, threshold, default_val):
    res = [default_val]
    for x in tup:
        if x < threshold:
            res.append(x)
    return tuple(res)


def get_blocked_traffic_lights_by_traffic_light(junction, blocking_traffic_light):
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
    blocked_traffic_lights = set()
    for blocking_traffic_light in blocking_traffic_lights:
        blocked_traffic_lights = blocked_traffic_lights | get_blocked_traffic_lights_by_traffic_light(junction, blocking_traffic_light)
    return blocked_traffic_lights


def solve_custom_knapsack(items, must_include, capacity: int, junction):
    best_reward = must_include.size
    best_combination = [must_include]

    def backtrack(index: int, included, total_reward: int, total_weight: int):
        nonlocal best_reward, best_combination

        # Base case: reached end
        if index == len(items):
            if must_include in included and total_weight <= capacity:
                if total_reward > best_reward:
                    best_reward = total_reward
                    best_combination = list(included)
            return

        item = items[index]

        # must_include already in included
        if item is must_include:
            backtrack(index + 1, included, total_reward, total_weight)
        else:
            next_included = included | {item}
            weight = item.get_weight(included, junction)
            if total_weight + weight <= capacity:
                backtrack(index + 1, next_included, total_reward + item.size, total_weight + weight)

            backtrack(index + 1, included, total_reward, total_weight)

    # Start recursion
    init_included = set()
    init_included.add(must_include)
    backtrack(0, init_included, best_reward, must_include.get_weight(set(), junction))
    return best_reward, best_combination

def sort_and_remove_duplicates_in_tuple(tup): # tup: tuple
    if not isinstance(tup, tuple):
        raise TypeError("tup is invalid: Not a tuple")
    return remove_duplicates_in_tuple(sort_tuple(tup))


def sort_tuple(tup): # tup: tuple
    if not isinstance(tup, tuple):
        raise TypeError("tup is invalid: Not a tuple")
    return tuple(sorted(tup))


def remove_duplicates_in_tuple(tup): # tup: tuple (sorted)
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
