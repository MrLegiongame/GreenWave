import random
import threading
import time

from classes.Enums.Alg import Alg


class Algorithm:
    def __init__(self, alg=None, nodes=None):
        self.alg = alg
        self.nodes = nodes
        self.nodes_size = len(nodes)
        self.terminate_flag = False

    def set(self, alg, nodes):
        self.alg = alg
        self.nodes = nodes

    def update_fixed_timing_cycle(self):
        time.sleep(2)
        threads = []
        for index in range(self.nodes_size):
            active_index = (self.nodes[index].active_index + 1) % self.nodes[index].states_size
            threads.append(threading.Thread(target=self.nodes[index].update_state, args=(active_index,)))
            threads[index].start()
        for index in range(self.nodes_size):
            threads[index].join()

    def update_adaptive_alg(self):
        threads = []
        start_time = time.time()
        for index in range(self.nodes_size):
            active_index = self.nodes[index].get_max_vehicle_count_state_index()
            threads.append(threading.Thread(target=self.nodes[index].update_state, args=(active_index,)))
            threads[index].start()
        for index in range(self.nodes_size):
            threads[index].join()
        end_time = time.time()
        delta_time = end_time - start_time
        if delta_time < 0.5:
            time.sleep(0.5 - delta_time)

    def update_green_wave(self):
        threads = []
        start_time = time.time()
        for index in range(self.nodes_size):
            active_index = self.nodes[index].get_max_score_state_index()
            threads.append(threading.Thread(target=self.nodes[index].update_state, args=(active_index,)))
            threads[index].start()
        for index in range(self.nodes_size):
            threads[index].join()
        end_time = time.time()
        delta_time = end_time - start_time
        if delta_time < 0.5:
            time.sleep(0.5 - delta_time)

    def update(self):
        match self.alg:
            case Alg.FIXED_TIMING_CYCLE:
                return self.update_fixed_timing_cycle()
            case Alg.ADAPTIVE_ALG:
                return self.update_adaptive_alg()
            case Alg.GREEN_WAVE:
                return self.update_green_wave()
            case _:
                print(f"Algorithm couldn't update due to invalid Alg")
                return None

    def run(self):
        for node in self.nodes:
            active_index = random.randint(0, node.states_size - 1)
            node.set_traffic_lights_states(active_index)
        while not self.terminate_flag:
            self.update()
