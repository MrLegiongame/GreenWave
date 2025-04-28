import networkx as nx
from networkx.algorithms.flow import capacity_scaling


def are_there_possible_collisions(lanes):
    #  TODO
    pass


def find_obj_index_in_array(obj, arr):
    if None is arr:
        return None
    i = 0
    for element in arr:
        if element is obj:
            return i
        i += 1
    return None


def create_flow_with_lane(inside, outside, direction_index, lane_index): # inside: tuple[Direction], outside: tuple[int]
    G = nx.DiGraph()
    V = ["S", "T"]
    E = []

    for direction in range(len(outside)):
        V.append(f"O{direction}")
        for i in outside[direction]:
            E.append((f"O{direction}", "T", i))

    for direction in range(len(inside)):
        for lane in range(len(inside[direction].direction)):
            V.append(f"I{direction}:{lane}")
            to_directions_amount = 0
            for to_direction in inside[direction].direction[lane].lane:
                E.append((f"I{direction}:{lane}", f"O{to_direction}", 1))
                to_directions_amount += 1
            E.append(("S", f"I{direction}:{lane}", to_directions_amount))

    G.add_nodes_from(V)
    G.add_edges_from(E)

    if not (None is direction_index or None is lane_index):
        G["S"][f"I{direction_index}:{lane_index}"]["flow"] = G["S"][f"I{direction_index}:{lane_index}"]["capacity"]  # sets the flow for edge S -> I
    return nx.maximum_flow(G, "S", "T", flow_func=capacity_scaling)


def create_state_from_flow(flow_dict, junction):
    state = []
    for connections in flow_dict:
        if connections[0][0] == "I":
            if connections[1][0][1] == 1:
                direction = int(connections[0][connections[0].find("I") + 1: connections[0].find(":")])
                lane = int(connections[0][connections[0].find(":") + 1:])
                state.append(junction.inside[direction].direction[lane])
    return tuple(state)


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
