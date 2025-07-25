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
            if hasattr(vehicle, 'has_arrived') and vehicle.has_arrived():
                continue
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
        G = nx.DiGraph()

        # Add edges (automatically adds nodes too)
        for junction in self.nodes:
            for direction in junction.directions:
                for in_lane in direction.in_lanes:
                    in_lane_name = "InLane" + str(in_lane.index_in_map)
                    for to_lane in in_lane.to_lanes:
                        out_lane_name = "OutLane" + str(to_lane.index_in_map)
                        G.add_edge(in_lane_name, out_lane_name, weight=0)
                       # print(f"  Added edge: {in_lane_name} -> {out_lane_name} (weight=0)")

       # print("\n[DEBUG] Adding road connections:")
        for road in self.edges:
            length = road.length

            for out_lane in road.first_direction.out_lanes:
                for in_lane in road.second_direction.in_lanes:
                    out_lane_name = "OutLane" + str(out_lane.index_in_map)
                    in_lane_name = "InLane" + str(in_lane.index_in_map)
                    G.add_edge(out_lane_name, in_lane_name, weight=length)

            for out_lane in road.second_direction.out_lanes:
                for in_lane in road.first_direction.in_lanes:
                    out_lane_name = "OutLane" + str(out_lane.index_in_map)
                    in_lane_name = "InLane" + str(in_lane.index_in_map)
                    G.add_edge(out_lane_name, in_lane_name, weight=length)

            """
            # print(f"\nRoad {road.name} (length={length}):")
            
            # Get the direction indices from the road
            dir1_idx = road.first_direction.index_in_map
            dir2_idx = road.second_direction.index_in_map
            
            # Find the OUT lane from first direction and IN lane from second direction
            out_lane = None
            in_lane = None
            for direction in road.first_direction.parent_junction.directions:
                if direction.index_in_map == dir1_idx:
                    out_lane = direction.out_lanes[0]  # Each direction has one OUT lane
                    break
            for direction in road.second_direction.parent_junction.directions:
                if direction.index_in_map == dir2_idx:
                    in_lane = direction.in_lanes[0]  # Each direction has one IN lane
                    break
            
            if out_lane and in_lane:
                out_lane_name = "OutLane" + str(out_lane.index_in_map)
                in_lane_name = "InLane" + str(in_lane.index_in_map)
                G.add_edge(out_lane_name, in_lane_name, weight=length)
                #print(f"  Added edge: {out_lane_name} -> {in_lane_name} (weight={length})")
            
            # Find the OUT lane from second direction and IN lane from first direction
            out_lane = None
            in_lane = None
            for direction in road.second_direction.parent_junction.directions:
                if direction.index_in_map == dir2_idx:
                    out_lane = direction.out_lanes[0]  # Each direction has one OUT lane
                    break
            for direction in road.first_direction.parent_junction.directions:
                if direction.index_in_map == dir1_idx:
                    in_lane = direction.in_lanes[0]  # Each direction has one IN lane
                    break
            
            if out_lane and in_lane:
                out_lane_name = "OutLane" + str(out_lane.index_in_map)
                in_lane_name = "InLane" + str(in_lane.index_in_map)
                G.add_edge(out_lane_name, in_lane_name, weight=length)
                #print(f"  Added edge: {out_lane_name} -> {in_lane_name} (weight={length})")
                """

        # Print final graph structure
        # print("\n[DEBUG] Final graph structure:")
        # print(f"Number of nodes: {G.number_of_nodes()}")
        # print(f"Number of edges: {G.number_of_edges()}")
        # print("\nAll nodes:")
        # for node in sorted(G.nodes()):
        #     print(f"  {node}")
        # print("\nAll edges:")
        # for edge in sorted(G.edges(data=True)):
        #     print(f"  {edge[0]} -> {edge[1]} (weight={edge[2]['weight']})")

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
        
        print(f"\n[DEBUG] Finding path from {source} to {target}")
        print(f"Start lane index: {start.index_in_map}")
        print(f"End lane index: {end.index_in_map}")
        

        # Get node path
        try:
            lane_path = nx.shortest_path(self.graph, source=source, target=target, weight="weight")
            print(f"\nFound path: {lane_path}")
        # except nx.exception.NetworkXNoPath as e:
        except Exception as e:
            print(f"\nNo path available between {source} and {target}")
            # print("\nGraph structure:")
            # print("Nodes:", sorted(self.graph.nodes()))
            # print("\nEdges:")
            # for edge in sorted(self.graph.edges(data=True)):
            #     print(f"  {edge[0]} -> {edge[1]} (weight={edge[2]['weight']})")
            return None, None

        # Convert to list of edges (as tuples)
        for lane_str_index in range(len(lane_path)):
            lane_path[lane_str_index] = self.find_lane_by_index_in_map_str(lane_path[lane_str_index])
        edge_path = list(zip(lane_path[:-1], lane_path[1:]))
        print(f"Final path: {edge_path}")

        return lane_path, edge_path

    def find_road_lanes_by_lanes(self, in_lane):
        for road in self.edges:
            for road_lane in road.road_lanes_first_direction:
                if in_lane is road_lane.destination_lane:
                    return road_lane

            for road_lane in road.road_lanes_second_direction:
                if in_lane is road_lane.destination_lane:
                    return road_lane

        return None

    """
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
