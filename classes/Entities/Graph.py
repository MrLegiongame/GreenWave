"""
Graph Module

This module contains the Graph class and related functions for managing the traffic
network graph in the simulation system. The Graph class represents the complete
traffic network with nodes (junctions), edges (roads), and vehicles, providing
pathfinding capabilities and visualization support.

Classes:
    Graph: Represents the complete traffic network with pathfinding capabilities.

Functions:
    find_out_lane_by_index_in_junction: Helper function to find output lanes in junctions.
"""

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
    """
    Find an output lane in a junction by its index.
    
    Args:
        junction (Junction): The junction to search in
        out_lane_index (int): The index of the output lane to find
        
    Returns:
        Lane or None: The found output lane, or None if not found
    """
    for direction in junction.directions:
        for out_lane in direction.out_lanes:
            if out_lane_index == out_lane.index_in_junction:
                return out_lane
    return None


class Graph:
    """
    Represents the complete traffic network with nodes, edges, and vehicles.
    
    The Graph class manages the entire traffic simulation network, including
    junctions (nodes), roads (edges), and vehicles. It provides pathfinding
    capabilities using NetworkX for optimal route calculation and supports
    visualization of the network using Pygame.
    
    Attributes:
        nodes (list): List of junction nodes in the network
        nodes_size (int): Number of nodes in the network
        edges (list): List of road edges connecting nodes
        edges_size (int): Number of edges in the network
        vehicles (list): List of vehicles in the simulation
        vehicles_size (int): Number of vehicles in the simulation
        dt (float): Delta time for simulation updates
        graph (networkx.DiGraph): NetworkX graph for pathfinding
    """

    def __init__(self, nodes, edges, vehicles, dt=0):
        """
        Initialize a new Graph instance.
        
        Args:
            nodes (list): List of junction nodes
            edges (list): List of road edges
            vehicles (list): List of vehicles
            dt (float, optional): Delta time for simulation updates. Defaults to 0.
        """
        self.nodes = None
        self.nodes_size = None
        self.edges = None
        self.edges_size = None
        self.vehicles = None
        self.dt = dt
        self.vehicles_size = None
        self.graph = None  # used for path finding logic
        if True:
            self.nodes = nodes
            self.nodes_size = len(nodes)
            self.edges = edges
            self.edges_size = len(edges)
            self.vehicles = vehicles
            self.vehicles_size = len(vehicles)
            self.set_graph_for_path()

    def draw(self, screen, sim):
        """
        Draw the traffic network on the provided screen.
        
        Args:
            screen: Pygame screen surface to draw on
            sim: Simulation object containing current state information
            
        Note:
            This method draws:
            - White lines for road edges
            - Grey circles for junctions (green for current junction)
            - Red circles for vehicles (excluding arrived vehicles)
        """
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
        """
        Get neighboring nodes and edge weights for a given node.
        
        Args:
            node: The source node to find neighbors for
            default: Default value to return if no neighbors found
            
        Returns:
            list or default: List of (neighbor_node, edge_weight) tuples, or default value
        """
        neighbors = []
        for edge in self.edges:
            src = edge.source_direction.parent_junction
            dst = edge.destination_direction.parent_junction
            if src is node:
                neighbors.append((dst, edge.length))  # include weight
        return neighbors if neighbors else default

    def set_graph_for_path(self):
        """
        Create a NetworkX directed graph for pathfinding.
        
        This method constructs a NetworkX DiGraph representation of the traffic
        network, where nodes represent lanes and edges represent connections
        between lanes. The graph is used for finding optimal routes between
        any two points in the network.
        
        Returns:
            networkx.DiGraph: The constructed graph for pathfinding
            
        Note:
            The graph includes both junction connections (weight=0) and road
            connections (weight=road_length) to enable accurate pathfinding.
        """
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
        """
        Find a lane object by its string representation in the graph.
        
        Args:
            lane_str (str): String representation of the lane (e.g., "InLane123", "OutLane456")
            
        Returns:
            Lane or None: The found lane object, or None if not found
            
        Note:
            The lane_str should start with "InLane" or "OutLane" followed by the index.
        """
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
        """
        Find the optimal path between two lanes using NetworkX shortest path algorithm.
        
        Args:
            start (Lane): The starting lane
            end (Lane): The destination lane
            
        Returns:
            tuple: (lane_path, edge_path) where:
                - lane_path: List of Lane objects representing the path
                - edge_path: List of (lane, lane) tuples representing edges
                
        Note:
            Returns (None, None) if no path is available between the specified lanes.
            The method uses NetworkX's shortest_path algorithm with edge weights.
        """
        import networkx as nx

        # Create node identifiers for NetworkX graph
        source = "OutLane" + str(start.index_in_map)
        target = "InLane" + str(end.index_in_map)
        
        print(f"\n[DEBUG] Finding path from {source} to {target}")
        print(f"Start lane index: {start.index_in_map}")
        print(f"End lane index: {end.index_in_map}")
        

        # Get node path using NetworkX shortest path algorithm
        try:
            lane_path = nx.shortest_path(self.graph, source=source, target=target, weight="weight")
            print(f"\nFound path: {lane_path}")
        except Exception as e:
            print(f"\nNo path available between {source} and {target}")
            return None, None

        # Convert string node names back to Lane objects
        for lane_str_index in range(len(lane_path)):
            lane_path[lane_str_index] = self.find_lane_by_index_in_map_str(lane_path[lane_str_index])
        
        # Create edge path from lane path (consecutive pairs)
        edge_path = list(zip(lane_path[:-1], lane_path[1:]))
        print(f"Final path: {edge_path}")

        return lane_path, edge_path

    def find_road_lanes_by_lanes(self, in_lane):
        """
        Find the road lane that connects to a specific input lane.
        
        Args:
            in_lane (Lane): The input lane to find the connecting road lane for
            
        Returns:
            RoadLane or None: The connecting road lane, or None if not found
            
        Note:
            This method searches through all roads and their lanes to find
            which road lane serves as the destination for the given input lane.
        """
        for road in self.edges:
            for road_lane in road.road_lanes_first_direction:
                if in_lane is road_lane.destination_lane:
                    return road_lane

            for road_lane in road.road_lanes_second_direction:
                if in_lane is road_lane.destination_lane:
                    return road_lane

        return None
