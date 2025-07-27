"""
Algorithm Module

This module contains the Algorithm class for managing traffic light control algorithms
in the traffic simulation system. The Algorithm class implements different traffic
control strategies including fixed timing cycles, adaptive algorithms, and green wave
algorithms for energy and pollution optimization.

Classes:
    Algorithm: Manages traffic light control algorithms and state transitions.
"""

import random
import threading
import time

from classes.Enums.Alg import Alg


class Algorithm:
    """
    Manages traffic light control algorithms and coordinates state transitions
    across multiple junctions in the traffic simulation system.
    
    The Algorithm class supports multiple traffic control strategies including
    fixed timing cycles, adaptive algorithms based on vehicle counts, and green
    wave algorithms optimized for energy consumption or pollution reduction.
    
    Attributes:
        alg (Alg): The current algorithm type being used for traffic control
        nodes (list): List of junction nodes to be controlled by this algorithm
        nodes_size (int): Number of nodes being managed
        threads (list): List of threads for concurrent state updates
        terminate_flag (bool): Flag to signal algorithm termination
    """

    def __init__(self, alg=None, nodes=None):
        """
        Initialize a new Algorithm instance.
        
        Args:
            alg (Alg, optional): The algorithm type to use for traffic control
            nodes (list, optional): List of junction nodes to control
        """
        self.alg = alg
        self.nodes = nodes
        self.nodes_size = len(nodes)
        self.threads = [None] * self.nodes_size  # Thread for each node to allow concurrent updates
        self.terminate_flag = False

    def get_next_active_index(self, index):
        """
        Determine the next active state index for a specific junction based on the current algorithm.
        
        Args:
            index (int): Index of the junction node to update
            
        Returns:
            int or None: The next active state index, or None if algorithm is invalid
            
        Note:
            This method implements different logic based on the algorithm type:
            - FIXED_TIMING_CYCLE: Cycles through states sequentially
            - ADAPTIVE_ALG: Chooses state with maximum vehicle count
            - GREEN_WAVE_ENERGY: Optimizes for energy consumption
            - GREEN_WAVE_POLLUTION: Optimizes for pollution reduction
        """
        match self.alg:
            case Alg.FIXED_TIMING_CYCLE:
                # Fixed timing: simply cycle to the next state
                time.sleep(2)
                next_active_index = (self.nodes[index].active_index + 1) % self.nodes[index].states_size
            case Alg.ADAPTIVE_ALG:
                # Adaptive: choose the state with the most vehicles waiting
                next_active_index = self.nodes[index].get_max_vehicle_count_state_index()
            case Alg.GREEN_WAVE_ENERGY:
                # GreenWave energy: choose the state with the minimum expected energy consumption prediction
                next_active_index = self.nodes[index].get_min_expected_filter_state_index("energy")
            case Alg.GREEN_WAVE_POLLUTION:
                # GreenWave pollution: choose the state with the minimum expected pollution prediction
                next_active_index = self.nodes[index].get_min_expected_filter_state_index("pollution")
            case _:
                # Algorithm couldn't be found
                next_active_index = self.nodes[index].active_index

        self.nodes[index].update_state(next_active_index)

    def update(self):
        """
        Update all junction states concurrently using threading.
        
        This method creates threads for each junction that needs a state update
        and ensures a minimum update interval of 0.1 seconds for stability.
        
        Note:
            Only junctions that are not preventing state changes will be updated.
            Each junction update runs in its own thread for concurrent processing.
        """
        start_time = time.time()
        for index in range(self.nodes_size):
            if not self.nodes[index].prevent_state_change:
                self.nodes[index].prevent_state_change = True
                # Launch a thread to update this node's state concurrently
                self.threads[index] = (threading.Thread(target=self.get_next_active_index, args=(index,)))
                self.threads[index].start()
        end_time = time.time()
        delta_time = end_time - start_time
        if delta_time < 0.1:
            # Ensure a minimum update interval for stability
            time.sleep(0.1 - delta_time)

    def run(self):
        """
        Run the traffic control algorithm continuously until terminated.
        
        This method initializes all junctions with random states and then
        continuously updates them using the specified algorithm until the
        terminate_flag is set to True.
        
        Note:
            The algorithm runs in an infinite loop until explicitly terminated.
            Initial states are randomly assigned to provide variety in the simulation.
        """
        for node in self.nodes:
            # Randomly initialize each node's state for simulation variety
            active_index = random.randint(0, node.states_size - 1)
            node.set_traffic_lights_states(active_index)
        while not self.terminate_flag:
            # Continuously update all nodes until termination is requested
            self.update()
