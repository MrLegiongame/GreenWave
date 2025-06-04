import networkx as nx
from networkx.algorithms.flow import capacity_scaling, build_residual_network



def are_there_possible_collisions(lanes):
    #  TODO
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
            print(flow_dict[u][v])
            if flow_graph.has_edge(u, v) and 0 != flow_graph[u][v]["capacity"]:
                flow_graph[u][v]["flow"] = flow_dict[u][v]


def create_flow_with_traffic_light(flow_graph, traffic_light_index):

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

    flow_value, flow_dict = capacity_scaling(flow_graph, "S", "T")
    apply_flow_to_graph(flow_graph, flow_dict)

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

    return flow_graph


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
