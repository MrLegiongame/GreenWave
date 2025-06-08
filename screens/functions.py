import networkx as nx
from networkx.algorithms.flow import capacity_scaling, build_residual_network



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


def get_to_lanes_amount_in_traffic_light(traffic_light):
    amount = 0
    for lane in traffic_light.lanes:
        amount += lane.size
    return amount


def create_flow_graph(traffic_lights):  # for states creation use
    G = nx.DiGraph()
    G.add_nodes_from(["S", "T"])
    traffic_lights = list(traffic_lights)

    for traffic_light_index in range(len(traffic_lights)):
        traffic_light = traffic_lights[traffic_light_index]
        to_lanes_amount_in_group = get_to_lanes_amount_in_traffic_light(traffic_light)
        G.add_node(f"TL{traffic_light_index}")
        G.add_edge("S", f"TL{traffic_light_index}", capacity=to_lanes_amount_in_group, flow=0)
        for lane_index in range(traffic_light.size):
            lane = traffic_light.lanes[lane_index]
            to_lanes_amount = lane.size
            G.add_node(f"I{traffic_light_index}:{lane_index}")
            G.add_edge(f"TL{traffic_light_index}", f"I{traffic_light_index}:{lane_index}", capacity=to_lanes_amount, flow=0)
            for to_lane_index in range(to_lanes_amount):
                G.add_node(f"O{traffic_light_index}:{lane_index}:{to_lane_index}")
                G.add_edge(f"I{traffic_light_index}:{lane_index}", f"O{traffic_light_index}:{lane_index}:{to_lane_index}", capacity=1, flow=0)

                G.add_edge(f"O{traffic_light_index}:{lane_index}:{to_lane_index}", "T", capacity=1, flow=0)

    return G


def apply_flow_to_graph(flow_graph, flow_dict):
    for u in flow_dict:
        for v in flow_dict[u]:
            print(flow_dict[u][v])  # TODO: delete code line later- used for debug
            if flow_graph.has_edge(u, v):
                flow_graph[u][v]["flow"] += flow_dict[u][v]


def print_flow_graph_data(flow_graph):
    traffic_lights_neighbors = flow_graph.successors("S")
    for tl_index in range(len(list(traffic_lights_neighbors))):
        print(f"S->TL{tl_index} flow: {flow_graph['S'][f'TL{tl_index}']['flow']}, capacity: {flow_graph['S'][f'TL{tl_index}']['capacity']}")
        lanes_neighbors = flow_graph.successors(f"TL{tl_index}")
        for lane_index in range(len(list(lanes_neighbors))):
            print(f"TL{tl_index}->I{tl_index}:{lane_index} flow: {flow_graph[f'TL{tl_index}'][f'I{tl_index}:{lane_index}']['flow']}, capacity: {flow_graph[f'TL{tl_index}'][f'I{tl_index}:{lane_index}']['capacity']}")
            to_lanes_neighbors = flow_graph.successors(f"I{tl_index}:{lane_index}")
            for to_lane_index in range(len(list(to_lanes_neighbors))):
                print(f"I{tl_index}:{lane_index}->O{tl_index}:{lane_index}:{to_lane_index} flow: {flow_graph[f'I{tl_index}:{lane_index}'][f'O{tl_index}:{lane_index}:{to_lane_index}']['flow']}, capacity: {flow_graph[f'I{tl_index}:{lane_index}'][f'O{tl_index}:{lane_index}:{to_lane_index}']['capacity']}")
                print(f"O{tl_index}:{lane_index}:{to_lane_index}->T flow: {flow_graph[f'O{tl_index}:{lane_index}:{to_lane_index}']['T']['flow']}, capacity: {flow_graph[f'O{tl_index}:{lane_index}:{to_lane_index}']['T']['capacity']}")


def create_flow_with_traffic_light(flow_graph, traffic_light_index):
    """
    print("Before")  # TODO: delete code line later- used for debug
    print_flow_graph_data(flow_graph)  # TODO: delete code line later- used for debug
    print()  # TODO: delete code line later- used for debug

    capacities = {f"TL{traffic_light_index}": flow_graph["S"][f"TL{traffic_light_index}"]["capacity"]}

    flow_graph["S"][f"TL{traffic_light_index}"]["capacity"] = 0
    lanes_neighbors = flow_graph.successors(f"TL{traffic_light_index}")
    for lane_index in range(len(list(lanes_neighbors))):
        capacities[f"I{traffic_light_index}:{lane_index}"] = flow_graph[f"TL{traffic_light_index}"][f"I{traffic_light_index}:{lane_index}"]["capacity"]
        flow_graph[f"TL{traffic_light_index}"][f"I{traffic_light_index}:{lane_index}"]["capacity"] = 0
        to_lanes_neighbors = flow_graph.successors(f"I{traffic_light_index}:{lane_index}")
        for to_lane_index in range(len(list(to_lanes_neighbors))):
            capacities[f"O{traffic_light_index}:{lane_index}:{to_lane_index}"] = flow_graph[f"I{traffic_light_index}:{lane_index}"][f"O{traffic_light_index}:{lane_index}:{to_lane_index}"]["capacity"]
            capacities[f"T{traffic_light_index}:{lane_index}:{to_lane_index}"] = flow_graph[f"O{traffic_light_index}:{lane_index}:{to_lane_index}"]["T"]["capacity"]
            flow_graph[f"I{traffic_light_index}:{lane_index}"][f"O{traffic_light_index}:{lane_index}:{to_lane_index}"]["capacity"] = 0
            flow_graph[f"O{traffic_light_index}:{lane_index}:{to_lane_index}"]["T"]["capacity"] = 0

    print_flow_graph_data(flow_graph)  # TODO: delete code line later- used for debug
    flow_value, flow_dict = capacity_scaling(flow_graph, "S", "T")
    print(flow_dict)  # TODO: delete code line later- used for debug
    print("After capacity_scaling")  # TODO: delete code line later- used for debug
    print_flow_graph_data(flow_graph)  # TODO: delete code line later- used for debug
    print()  # TODO: delete code line later- used for debug
    apply_flow_to_graph(flow_graph, flow_dict)
    print("After apply_flow_to_graph")  # TODO: delete code line later- used for debug
    print_flow_graph_data(flow_graph)  # TODO: delete code line later- used for debug
    print()  # TODO: delete code line later- used for debug

    # Build residual network before restoring capacities
    residual = build_residual_network(flow_graph, capacity="capacity")
    print_residual_flows(residual)  # TODO: delete code line later- used for debug
    flow_value, flow_dict = capacity_scaling(residual, "S", "T")
    apply_flow_to_graph(flow_graph, flow_dict)
    print_flow_graph_data(flow_graph)  # TODO: delete code line later- used for debug

    # Now restore capacities and set flows
    flow_graph["S"][f"TL{traffic_light_index}"]["capacity"] = capacities[f"TL{traffic_light_index}"]
    flow_graph["S"][f"TL{traffic_light_index}"]["flow"] = flow_graph["S"][f"TL{traffic_light_index}"]["capacity"]
    lanes_neighbors = flow_graph.successors(f"TL{traffic_light_index}")
    for lane_index in range(len(list(lanes_neighbors))):
        flow_graph[f"TL{traffic_light_index}"][f"I{traffic_light_index}:{lane_index}"]["capacity"] = capacities[f"I{traffic_light_index}:{lane_index}"]
        flow_graph[f"TL{traffic_light_index}"][f"I{traffic_light_index}:{lane_index}"]["flow"] = flow_graph[f"TL{traffic_light_index}"][f"I{traffic_light_index}:{lane_index}"]["capacity"]
        to_lanes_neighbors = flow_graph.successors(f"I{traffic_light_index}:{lane_index}")
        for to_lane_index in range(len(list(to_lanes_neighbors))):
            flow_graph[f"I{traffic_light_index}:{lane_index}"][f"O{traffic_light_index}:{lane_index}:{to_lane_index}"]["capacity"] = capacities[f"O{traffic_light_index}:{lane_index}:{to_lane_index}"]
            flow_graph[f"O{traffic_light_index}:{lane_index}:{to_lane_index}"]["T"]["capacity"] = capacities[f"T{traffic_light_index}:{lane_index}:{to_lane_index}"]
            flow_graph[f"I{traffic_light_index}:{lane_index}"][f"O{traffic_light_index}:{lane_index}:{to_lane_index}"]["flow"] = flow_graph[f"I{traffic_light_index}:{lane_index}"][f"O{traffic_light_index}:{lane_index}:{to_lane_index}"]["capacity"]
            flow_graph[f"O{traffic_light_index}:{lane_index}:{to_lane_index}"]["T"]["flow"] = flow_graph[f"O{traffic_light_index}:{lane_index}:{to_lane_index}"]["T"]["capacity"]

    print("After adjusting flow")  # TODO: delete code line later- used for debug
    print_flow_graph_data(flow_graph) # TODO: delete code line later- used for debug
    """

    flow_graph["S"][f"TL{traffic_light_index}"]["flow"] = flow_graph["S"][f"TL{traffic_light_index}"]["capacity"]
    lanes_neighbors = flow_graph.successors(f"TL{traffic_light_index}")
    for lane_index in range(len(list(lanes_neighbors))):
        flow_graph[f"TL{traffic_light_index}"][f"I{traffic_light_index}:{lane_index}"]["flow"] = flow_graph[f"TL{traffic_light_index}"][f"I{traffic_light_index}:{lane_index}"]["capacity"]
        to_lanes_neighbors = flow_graph.successors(f"I{traffic_light_index}:{lane_index}")
        for to_lane_index in range(len(list(to_lanes_neighbors))):
            flow_graph[f"I{traffic_light_index}:{lane_index}"][f"O{traffic_light_index}:{lane_index}:{to_lane_index}"]["flow"] = flow_graph[f"I{traffic_light_index}:{lane_index}"][f"O{traffic_light_index}:{lane_index}:{to_lane_index}"]["capacity"]
            flow_graph[f"O{traffic_light_index}:{lane_index}:{to_lane_index}"]["T"]["flow"] = flow_graph[f"O{traffic_light_index}:{lane_index}:{to_lane_index}"]["T"]["capacity"]

    print()
    residual = build_residual_network(flow_graph, capacity="flow")
    print_residual_flows(residual)  # TODO: delete code line later- used for debug
    flow_value, flow_dict = capacity_scaling(residual, "S", "T")
    apply_flow_to_graph(flow_graph, flow_dict)
    print_flow_graph_data(flow_graph)  # TODO: delete code line later- used for debug
    return flow_graph


def print_residual_flows(residual_graph):
    print("Residual Graph Edge Flows:")
    print(list(residual_graph.edges(data=True)))
    for u, v, data in residual_graph.edges(data=True):
        capacity = data.get("capacity", 0)
        reverse_edge = data.get("reverse_edge")

        # The "flow" here is conceptual: if edge exists only because reverse flow exists
        is_forward = data.get("residual", True)
        if is_forward and reverse_edge:
            reverse_capacity = reverse_edge.get("capacity", 0)
            flow = reverse_capacity  # reverse edge capacity = actual flow on original edge
            print(f"{u} → {v} | residual capacity: {capacity} | flow: {flow}")


def create_state_from_flow(flow_graph, traffic_lights):
    state = set()

    traffic_lights = list(traffic_lights)

    for traffic_light_index in range(len(traffic_lights)):
        traffic_light = traffic_lights[traffic_light_index]
        if flow_graph["S"][f"TL{traffic_light_index}"]["flow"] == flow_graph["S"][f"TL{traffic_light_index}"]["capacity"]:
            state.add(traffic_light)
    return tuple(state)


def reset_graph_flow(flow_graph):
    traffic_light_neighbors = flow_graph.successors("S")
    for traffic_light_index in range(len(list(traffic_light_neighbors))):
        flow_graph["S"][f"TL{traffic_light_index}"]["flow"] = 0
        lanes_neighbors = flow_graph.successors(f"TL{traffic_light_index}")
        for lane_index in range(len(list(lanes_neighbors))):
            flow_graph[f"TL{traffic_light_index}"][f"I{traffic_light_index}:{lane_index}"]["flow"] = 0
            to_lanes_neighbors = flow_graph.successors(f"I{traffic_light_index}:{lane_index}")
            for to_lane_index in range(len(list(to_lanes_neighbors))):
                flow_graph[f"I{traffic_light_index}:{lane_index}"][f"O{traffic_light_index}:{lane_index}:{to_lane_index}"]["flow"] = 0
                flow_graph[f"O{traffic_light_index}:{lane_index}:{to_lane_index}"]["T"]["flow"] = 0


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
