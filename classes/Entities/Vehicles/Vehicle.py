import math
import os
import time
from abc import ABC
from classes.Entities.Point import Point
import pygame


def get_image_list(folder_path):
    supported_exts = (".png", ".jpg", ".jpeg", ".jfif", ".webp")
    return [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.lower().endswith(supported_exts)
    ]


class Vehicle(ABC):
    def __init__(self, length, weight, start_road, end_road, image, vehicle_type, energy_type, maximum_speed, acceleration=0):
        self.length = length
        self.weight = weight
        self.start_road = start_road
        self.cur_road = start_road
        self.end_road = end_road
        self.start_point = Point(start_road.get_first_point())
        self.cur_point = self.start_point
        self.end_point = Point(end_road.get_second_point())
        self.vehicle_type = vehicle_type
        self.energy_type = energy_type
        self.maximum_speed = maximum_speed
        self.velocity = min(self.cur_road.maximum_speed, self.maximum_speed)
        self.acceleration = acceleration

        if isinstance(image, str):
            self.image = pygame.image.load(image).convert_alpha()
        else:
            self.image = image

        self.distance_on_road_lane = 0
        self.nodes_path = []
        self.edges_path = []
        self.nodes_path_index = 0
        self.__next_junction_point = None
        self.__junctions_passed = 0
        self.__last_distance_to_next_junction = None
        self.__last_move_time_stamp = None

        # Stats
        self.total_time = 0
        self.total_energy_consumed = 0
        self.total_pollution = 0
        self.total_distance = 0

        print(
            f"[Vehicle Init] {vehicle_type} with {energy_type} created from {start_road.first_direction.parent_junction.point} "
            f"to {end_road.second_direction.parent_junction.point}")
        print(f"[Vehicle Init] cur_point: {self.cur_point}")

    def set_path(self, graph):
        start_node = self.start_road.first_direction.parent_junction
        end_node = self.end_road.second_direction.parent_junction
        if start_node is end_node:
            end_node = self.end_road.first_direction.parent_junction
        self.nodes_path, self.edges_path = graph.get_path(start_node, end_node)

        # if not self.nodes_path:
        #     # print(f"[set_path] No path found for vehicle from {self.start_road} to {self.end_road}")
        #     self.nodes_path = []
        #     self.__next_junction_point = None
        #     return

        # print(f"[set_path] Path set for vehicle from {self.start_road} to {self.end_road}")
        # print(f"[set_path] Path contains {len(self.nodes_path)} steps.")
        self.nodes_path_index = 1 if len(self.nodes_path) > 1 else 0
        self.__next_junction_point = (self.nodes_path[self.nodes_path_index]).point

    def __is_passed_junction(self):
        return self.__last_distance_to_next_junction < self.cur_point.get_distance_from_point(
            self.__next_junction_point)

    def move(self, dt):
        if None is self.__last_move_time_stamp:
            self.__last_move_time_stamp = time.time()

        if None is self.__next_junction_point:
            if len(self.nodes_path) == 1:
                self.__next_junction_point = self.nodes_path[0].point
            elif len(self.nodes_path) > 1:
                self.__next_junction_point = self.nodes_path[1].point

        if self.__last_distance_to_next_junction is None and self.__next_junction_point:
            self.__last_distance_to_next_junction = self.cur_point.get_distance_from_point(self.__next_junction_point)

        # gets current maximum possible AND legally velocity
        self.velocity = min(self.cur_road.maximum_speed, self.maximum_speed)

        # dt = time.time() - self.__last_move_time_stamp
        distance = self.velocity * dt + self.acceleration * (dt ** 2) / 2
        dx = self.__next_junction_point.x - self.cur_point.x
        dy = self.__next_junction_point.y - self.cur_point.y
        length = math.hypot(dx, dy)

        if length != 0:
            dx /= length
            dy /= length
        else:  # if direction to drive is exactly vertical or horizontal
            dx, dy = 1, 1

        new_x = self.cur_point.x + dx * distance
        new_y = self.cur_point.y + dy * distance

        if self.__is_passed_junction() or self.cur_point.get_distance_from_point(self.__next_junction_point) < 5:
            if self.nodes_path_index < len(self.nodes_path) - 1:
                self.nodes_path_index += 1
                self.__next_junction_point = self.nodes_path[self.nodes_path_index].point
                self.__last_distance_to_next_junction = self.cur_point.get_distance_from_point(
                    self.__next_junction_point)
            else:
                # print(f"[Vehicle] Reached final junction.")
                return

        self.cur_point = Point(new_x, new_y)
        self.__last_move_time_stamp = time.time()
        self.__last_distance_to_next_junction = self.cur_point.get_distance_from_point(self.__next_junction_point)
        self.velocity += self.acceleration * dt

        # print(f"[move] Vehicle new position: {self.cur_point.x:.2f}, {self.cur_point.y:.2f}")

    def __str__(self):
        return f"(x, y) = {self.get_cur_point()}"

    def get_cur_point(self):
        return self.cur_point
