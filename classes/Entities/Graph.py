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


def load_graph_from_json(sim, json_data):
    directions_in_map = []  # sorted by indexes in map

    # Extract junctions as nodes
    nodes = []
    junctions = json_data.get("Junctions", {})
    junction_index = 0
    for junction_name, junction_data in junctions.items():
        nodes.append(Junction())
        direction_index = 0
        for direction_name, direction_data in junction_data.items():
            direction = Direction(direction_data["Index_in_map"])
            direction.set_parent_junction(nodes[junction_index])
            nodes[junction_index].add_direction(direction)
            directions_in_map.append(direction)
            for out_lane_name, out_lane_index_in_junction in direction_data.get("Out_Lanes", {}).items():
                out_lane = Lane(LaneFacing.OUT, index_in_junction=out_lane_index_in_junction)
                out_lane.set_parent_direction(direction)
                nodes[junction_index].directions[direction_index].add_to_left(out_lane)
            direction_index += 1
        junction_index += 1


    junction_index = 0
    for junction_name, junction_data in junctions.items():
        direction_index = 0
        for direction_name, direction_data in junction_data.items():
            direction = nodes[junction_index].directions[direction_index]
            for in_lane_name, in_lane_data in direction_data.get("In_Lanes", {}).items():
                to_lanes = []
                for to_lane_name, to_lane_index_in_junction in in_lane_data.get("To_Lanes", {}).items():
                    out_lane = find_out_lane_by_index_in_junction(nodes[junction_index], to_lane_index_in_junction)
                    to_lanes.append(out_lane)
                in_lane = Lane(LaneFacing.IN, to_lanes=to_lanes)
                in_lane.set_parent_direction(direction)
                nodes[junction_index].directions[direction_index].add_to_left(in_lane)
            direction_index += 1
        junction_index += 1

    # Extract roads as edges
    edges = []
    roads = json_data.get("Roads", {})
    for road_name, road_data in roads.items():
        first_direction = directions_in_map[road_data["direction1_index_in_map"]]
        second_direction = directions_in_map[road_data["direction2_index_in_map"]]
        length = road_data["length"]
        edges.append(Road(road_name, first_direction, second_direction, length))

    # Assume no vehicle data yet
    vehicles = []

    sim.force_directed_layout(nodes, edges)
    # Create and return Graph instance
    return Graph(nodes=nodes, edges=edges, vehicles=vehicles)



class Graph:
    def __init__(self, nodes, edges, vehicles):
        self.nodes = None
        self.nodes_size = None
        self.edges = None
        self.edges_size = None
        self.vehicles = None
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
            vehicle.move()
            pygame.draw.circle(screen, Color.RED.value, vehicle.get_cur_point().get_point(), 6)

    def get(self, node, default=None):
        neighbors = []
        for edge in self.edges:
            src = edge.source_direction.parent_junction
            dst = edge.destination_direction.parent_junction
            if src is node:
                neighbors.append((dst, edge.length))  # include weight
        return neighbors if neighbors else default

    def get_path(self, start_road, end_road):
        start_junction = start_road.first_direction.parent_junction
        end_junction = end_road.second_direction.parent_junction

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

        return []  # No path found
