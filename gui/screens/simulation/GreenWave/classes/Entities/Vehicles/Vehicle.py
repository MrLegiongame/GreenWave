import math
from abc import ABC, abstractmethod
import os
import time
import heapq
from collections import deque
from classes.Entities.Point import Point


def get_image_list(folder_path):
    supported_exts = (".png", ".jpg", ".jpeg", ".jfif", ".webp")
    return [f for f in os.listdir(folder_path) if f.lower().endswith(supported_exts)]


def bfs_shortest_path(graph, start, end):
    queue = deque([(start, [start], [])])  # (current_node, path_nodes, path_edges)
    visited = set()

    while queue:
        current_node, path_nodes, path_edges = queue.popleft()

        if current_node == end:
            return path_nodes, path_edges

        visited.add(current_node)

        for edge in graph.edges:
            src = edge.source_direction.parent_junction
            dst = edge.destination_direction.parent_junction

            if src == current_node and dst not in visited:
                queue.append((dst, path_nodes + [dst], path_edges + [edge]))
                visited.add(dst)

    return None, None  # No path found


class Vehicle(ABC):
    def __init__(self, length, engine, weight, start_road, end_road, image):
        self.velocity = 0
        self.length = length
        self.engine = engine
        self.weight = weight
        self.start_road = start_road
        self.cur_road = start_road
        self.end_road = end_road
        self.start_point = Point(start_road.get_first_point())
        self.cur_point = self.start_point
        self.end_point = Point(end_road.get_second_point())
        self.image = image
        self.nodes_path = None
        self.edges_path = None
        self.road_lane = None
        self.distance_on_road_lane = 0

        self.__next_junction_point = None
        self.__junctions_passed = 0
        self.__last_distance_to_next_junction = None
        self.__last_move_time_stamp = None

        # for statistics
        self.total_time = 0
        self.total_energy_consumed = 0
        self.total_pollution = 0
        self.total_distance = 0

    def cross_junction(self):
        # TODO
        self.cur_road = self.edges_path[self.__junctions_passed]
        self.__next_junction_point = self.nodes_path[self.__junctions_passed].point
        self.__junctions_passed += 1

    def set_velocity(self, dt):
        if None is not self.engine.acceleration:
            self.velocity += self.engine.acceleration * dt

    def set_cur_road(self, road):
        self.cur_road = road

    def get_cur_point(self):
        return self.cur_point

    def set_cur_point(self, point):
        self.cur_point = point

    def set_path(self, graph):
        self.nodes_path, self.edges_path = bfs_shortest_path(graph, self.start_road.source_direction.parent_junction, self.end_road.destination_direction.parent_junction)

    def __is_passed_junction(self):
        return self.__last_distance_to_next_junction < self.cur_point.get_distance_from_point(self.__next_junction_point)

    def move(self):
        if None is self.__last_move_time_stamp:
            self.__last_move_time_stamp = time.time()

        if None is self.__next_junction_point:
            if 1 == len(self.nodes_path):
                self.__next_junction_point = self.nodes_path[0].point
            else:
                self.__next_junction_point = self.nodes_path[1].point

        if None is self.__last_distance_to_next_junction:
            self.__last_distance_to_next_junction = self.cur_point.get_distance_from_point(self.__next_junction_point)

        dt = time.time() - self.__last_move_time_stamp
        distance = self.velocity * dt + self.engine.calculate_acceleration() * (dt ** 2) / 2
        angle_in_rad = self.cur_road.get_slope_angle_in_rad()

        new_x = distance * math.cos(angle_in_rad)
        new_y = distance * math.sin(angle_in_rad)

        if (self.__is_passed_junction()):
            self.cross_junction()

        self.cur_point = Point(new_x, new_y)
        self.__last_move_time_stamp = time.time()

        self.__last_distance_to_next_junction = self.cur_point.get_distance_from_point(self.__next_junction_point)
        self.velocity = self.velocity + self.engine.calculate_acceleration() * dt

    def __str__(self):
        return f"(x, y) = {self.get_cur_point()}"
