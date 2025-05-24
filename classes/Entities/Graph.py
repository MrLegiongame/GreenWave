import json
from collections import deque

import pygame

from classes.Edges.Road import Road
from classes.Enums.Color import Color
from classes.Enums.LaneFacing import LaneFacing
from classes.Nodes.Direction import Direction
from classes.Nodes.Junction import Junction
from classes.Nodes.Lane import Lane


def find_out_lane_by_index_in_junction(junction, out_lane_index):
    for direction in junction.directions:
        for out_lane in direction.out_lanes:
            if out_lane_index == out_lane.index_in_junction:
                return out_lane
    return None


class Graph:
    def __init__(self, nodes, edges, vehicles, dt=0):

        self.nodes = None
        self.nodes_size = None
        self.edges = None
        self.edges_size = None
        self.vehicles = None
        self.dt = dt
        self.vehicles_size = None
        self.graph = None  # used for path finding logic
        if True:  # TODO change boolean statement
            self.nodes = nodes
            self.nodes_size = len(nodes)
            self.edges = edges
            self.edges_size = len(edges)
            self.vehicles = vehicles
            self.vehicles_size = len(vehicles)
            self.set_graph_for_path()

    def draw(self, screen, sim):
        # Draw edges
        for edge in self.edges:
            start_pos = edge.get_first_point()
            end_pos = edge.get_second_point()
            pygame.draw.line(screen, Color.WHITE.value, start_pos, end_pos, 3)

        # Draw nodes
        for node in self.nodes:
            pos = node.point.get_point()
            if sim.current_junction is node:
                pygame.draw.circle(screen, Color.DARK_GREEN.value, pos, 10)
            else:
                pygame.draw.circle(screen, Color.LIGHT_GREY.value, pos, 10)

        # Draw vehicles (without moving them)
        for vehicle in self.vehicles:
            pygame.draw.circle(screen, Color.RED.value, vehicle.get_cur_point().get_point(), 6)

    def get(self, node, default=None):
        neighbors = []
        for edge in self.edges:
            src = edge.source_direction.parent_junction
            dst = edge.destination_direction.parent_junction
            if src is node:
                neighbors.append((dst, edge.length))  # include weight
        return neighbors if neighbors else default

    def set_graph_for_path(self):
        import networkx as nx

        # Create a directed graph
        G = nx.DiGraph()  # use nx.DiGraph() for directed graphs

        # Add edges (automatically adds nodes too)
        for junction in self.nodes:
            for direction in junction.directions:
                for in_lane in direction.in_lanes:
                    in_lane_name = "InLane" + str(in_lane.index_in_map)
                    for to_lane in in_lane.to_lanes:
                        out_lane_name = "OutLane" + str(to_lane.index_in_map)
                        G.add_edge(in_lane_name, out_lane_name, weight=0)

        for road in self.edges:
            length = road.length
            for source_road_lane in road.road_lanes_first_direction:
                for destination_road_lane in road.road_lanes_first_direction:
                    out_lane_name = "OutLane" + str(source_road_lane.source_lane.index_in_map)
                    in_lane_name = "InLane" + str(destination_road_lane.destination_lane.index_in_map)
                    G.add_edge(out_lane_name, in_lane_name, weight=length)
            for source_road_lane in road.road_lanes_second_direction:
                for destination_road_lane in road.road_lanes_second_direction:
                    out_lane_name = "OutLane" + str(source_road_lane.source_lane.index_in_map)
                    in_lane_name = "InLane" + str(destination_road_lane.destination_lane.index_in_map)
                    G.add_edge(out_lane_name, in_lane_name, weight=length)

        self.graph = G
        return G

    def find_lane_by_index_in_map_str(self, lane_str):
        is_in_lane = lane_str.startswith("InLane")

        prefixes = ("InLane", "OutLane")
        matching_prefix = next((p for p in prefixes if lane_str.startswith(p)), None)
        index = int(lane_str[len(matching_prefix):])

        for junction in self.nodes:
            for direction in junction.directions:
                if is_in_lane:
                    for in_lane in direction.in_lanes:
                        if index == in_lane.index_in_map:
                            return in_lane
                else:
                    for out_lane in direction.out_lanes:
                        if index == out_lane.index_in_map:
                            return out_lane

        return None

    def get_path(self, start, end):
        import networkx as nx

        source = "OutLane" + str(start.index_in_map)
        target = "InLane" + str(end.index_in_map)

        # Get node path
        try:
            lane_path = nx.shortest_path(self.graph, source=source, target=target, weight="weight")
        except nx.exception.NetworkXNoPath as e:
            print("No path available between " + source + " and " + target + ", due to this error: " + str(e))
            return None, None

        # Convert to list of edges (as tuples)
        for lane_str_index in range(len(lane_path)):
            lane_path[lane_str_index] = self.find_lane_by_index_in_map_str(lane_path[lane_str_index])
        edge_path = list(zip(lane_path[:-1], lane_path[1:]))
        print(edge_path)

        return lane_path, edge_path

    def find_road_lanes_by_lanes(self, out_lane, in_lane):
        for road in self.edges:
            out_lane_found = False
            in_lane_found = False
            for road_lane in road.road_lanes_first_direction:
                if out_lane is road_lane.source_lane:
                    out_lane_found = True
                if in_lane is road_lane.destination_lane:
                    in_lane_found = True
            if out_lane_found and in_lane_found:
                return road.road_lanes_first_direction

            out_lane_found = False
            in_lane_found = False
            for road_lane in road.road_lanes_second_direction:
                if out_lane is road_lane.source_lane:
                    out_lane_found = True
                if in_lane is road_lane.destination_lane:
                    in_lane_found = True
            if out_lane_found and in_lane_found:
                return road.road_lanes_second_direction

        return None


"""
        # setup algorithm
        for node in self.nodes:
            node.distance = float('inf')  # infinity
            node.source_junction = None

        queue = deque()  # (current_node, path_nodes, path_edges)
        queue.append(start)
        start.distance = 0

        while queue:
            current_node = queue.popleft()
            for neighbor, edge in current_node.get_neighbors_junctions():
                if neighbor.distance > current_node.distance + edge.length:
                    neighbor.distance = current_node.distance + edge.length
                    neighbor.source_junction = current_node
                    queue.append(neighbor)

        current_node = end
        path_nodes = []
        path_edges = []
        while start is not current_node:
            path_nodes.insert(0, current_node)
            path_edges.insert(0, current_node.get_road_by_neighbor(current_node.source_junction))
            current_node = current_node.source_junction

        return path_nodes, path_edges
"""

"""
    def get_path(self, start_road, end_road):
        start_junction = start_road.first_direction.parent_junction
        end_junction = end_road.second_direction.parent_junction

        if start_junction is end_junction:
            end_junction = end_road.first_direction.parent_junction

        queue = deque([(start_junction, [start_junction])])
        visited = set()

        while queue:
            current_junction, path = queue.popleft()

            if current_junction == end_junction:
                return path  # return list of junctions

            visited.add(current_junction)

            for road in self.edges:
                src = road.first_direction.parent_junction
                dst = road.second_direction.parent_junction

                if src == current_junction and dst not in visited:
                    queue.append((dst, path + [dst]))


    def get_edge_list(self):
        return self.edges

        return []  # No path found
"""
