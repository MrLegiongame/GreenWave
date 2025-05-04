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
        if True:  # TODO change boolean statement
            self.nodes = nodes
            self.nodes_size = len(nodes)
            self.edges = edges
            self.edges_size = len(edges)
            self.vehicles = vehicles
            self.vehicles_size = len(vehicles)

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

        # Draw vehicles
        for vehicle in self.vehicles:
            vehicle.move(self.dt)
            pygame.draw.circle(screen, Color.RED.value, vehicle.get_cur_point().get_point(), 6)

    def get(self, node, default=None):
        neighbors = []
        for edge in self.edges:
            src = edge.source_direction.parent_junction
            dst = edge.destination_direction.parent_junction
            if src is node:
                neighbors.append((dst, edge.length))  # include weight
        return neighbors if neighbors else default

    def get_path(self, start, end):

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
