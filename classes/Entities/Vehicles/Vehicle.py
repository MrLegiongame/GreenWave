import math
import os
import random
import time
from abc import ABC
from classes.Entities.Point import Point
import pygame

from classes.Enums.LaneFacing import LaneFacing
from classes.Enums.State import State


def get_image_list(folder_path):
    supported_exts = (".png", ".jpg", ".jpeg", ".jfif", ".webp")
    return [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.lower().endswith(supported_exts)
    ]


class Vehicle(ABC):
    def __init__(self, length, weight, start_node, end_node, image, vehicle_type, energy_type, maximum_speed, acceleration=0):
        self.length = length
        self.weight = weight
        self.start_node = start_node
        self.cur_road_lane = None
        self.end_node = end_node
        self.start_point = start_node.point
        self.cur_point = self.start_point
        self.end_point = end_node.point
        self.vehicle_type = vehicle_type
        self.energy_type = energy_type
        self.maximum_speed = maximum_speed
        # self.velocity = min(self.cur_road_lane.maximum_speed, self.maximum_speed)
        self.velocity = None
        self.acceleration = acceleration

        if isinstance(image, str):
            self.image = pygame.image.load(image).convert_alpha()
        else:
            self.image = image

        self.distance_on_road_lane = 0
        self.lanes_path = []
        self.roads_path = []
        self.lanes_path_index = 0
        self.__end_in_lane = None
        self.__last_lane = None
        self.__lanes_passed = 0
        self.__last_distance_to_next_junction = None
        self.__last_move_time_stamp = None

        # Stats
        self.total_time = 0
        self.total_energy_consumed = 0
        self.total_pollution = 0
        self.total_distance = 0

        print(
            f"[Vehicle Init] {vehicle_type} with {energy_type} created from {self.start_point} "
            f"to {self.end_point}")
        print(f"[Vehicle Init] cur_point: {self.cur_point}")

    def set_path(self, graph):
        # start_node = self.start_road.first_direction.parent_junction
        # end_node = self.end_road.second_direction.parent_junction
        # if start_node is end_node:
        #     end_node = self.end_road.first_direction.parent_junction

        start_out_lane = None
        end_in_lane = None

        start_directions = self.start_node.directions.copy()
        while not start_out_lane:
            random_index = random.randrange(len(start_directions))
            if start_directions[random_index].out_lanes:
                start_out_lane = random.choice(start_directions[random_index].out_lanes)
            else:
                start_directions.pop(random_index)

        end_directions = self.end_node.directions.copy()
        while not end_in_lane:
            random_index = random.randrange(len(end_directions))
            if end_directions[random_index].in_lanes:
                end_in_lane = random.choice(end_directions[random_index].in_lanes)
            else:
                end_directions.pop(random_index)

        self.__end_in_lane = end_in_lane
        self.lanes_path, roads_path = graph.get_path(start_out_lane, end_in_lane)

        cur_road_lanes = []
        for lane1, lane2 in roads_path:
            if LaneFacing.IN == lane1.facing and LaneFacing.OUT == lane2.facing:
                in_lane = lane1
                out_lane = lane2
            elif LaneFacing.OUT == lane1.facing and LaneFacing.IN == lane2.facing:
                in_lane = lane2
                out_lane = lane1
            else:
                raise TypeError("set_path method is invalid: Invalid order in path: Lane with facing equals to None")
            cur_road_lanes.append(graph.find_road_lanes_by_lanes(out_lane=out_lane, in_lane=in_lane))
        self.cur_road_lane = cur_road_lanes[0]
        self.__last_lane = self.lanes_path[self.__lanes_passed]
        self.__lanes_passed += 1

    def __is_passed_junction(self):
        return self.__last_distance_to_next_junction < self.cur_point.get_distance_from_point(
            self.__next_junction_point)

    def move(self, dt):
        if None is self.__last_move_time_stamp:
            self.__last_move_time_stamp = time.time()

        if None is self.__last_lane:
            self.__last_lane = self.lanes_path[self.__lanes_passed]
            self.__lanes_passed += 1



        if LaneFacing.IN == self.__last_lane.facing:  # in a queue
            if self.__last_lane is self.__end_in_lane:  # if arrived in end lane
                return  # finish (seen as a code sink when a vehicle finished it's path)
            if True:  # TODO (self.__last_lane.cur_state in [State.GREEN, State.GREEN_FLICKERING]) and self is self.__last_lane.vehicles_queue[0]:  # if junction is available for crossing and the vehicle is the first in the lane's queue
                self.__last_lane = self.lanes_path[self.__lanes_passed]
                self.__lanes_passed += 1
                new_x, new_y = self.__last_lane.parent_junction.point.get_point()

        elif LaneFacing.OUT == self.__last_lane.facing:


            if True:  # TODO: if arrived in junction
                
                self.__last_lane = self.lanes_path[self.__lanes_passed]
                self.__lanes_passed += 1
                new_x, new_y = self.__last_lane.parent_junction.point.get_point()
        else:
            raise TypeError("move method is invalid: Invalid order in path: Lane with facing equals to None")

        self.cur_point = Point(new_x, new_y)
        self.__last_move_time_stamp = time.time()
        self.__last_distance_to_next_junction = self.cur_point.get_distance_from_point(
            self.lanes_path[self.__lanes_passed+1].parent_junction.point)
        self.velocity += self.acceleration * dt







        if self.__last_distance_to_next_junction is None and self.__next_junction_point:
            self.__last_distance_to_next_junction = self.cur_point.get_distance_from_point(self.__next_junction_point)

        # gets current maximum possible AND legally velocity
        self.velocity = min(self.cur_road_lane.maximum_speed, self.maximum_speed)

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
