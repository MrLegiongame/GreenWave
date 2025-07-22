import random
import threading
import time

from classes.Enums.Alg import Alg


class Algorithm:
    def __init__(self, alg=None, nodes=None):
        self.alg = alg
        self.nodes = nodes
        self.nodes_size = len(nodes)
        self.threads = [None] * self.nodes_size
        self.terminate_flag = False


    def set(self, alg, nodes):
        self.alg = alg
        self.nodes = nodes
        self.nodes_size = len(nodes)

    def get_next_active_index(self, index):
        match self.alg:
            case Alg.FIXED_TIMING_CYCLE:
                return (self.nodes[index].active_index + 1) % self.nodes[index].states_size
            case Alg.ADAPTIVE_ALG:
                return self.nodes[index].get_max_vehicle_count_state_index()
            case Alg.GREEN_WAVE_ENERGY:
                return self.nodes[index].get_min_expected_filter_state_index("energy")
            case Alg.GREEN_WAVE_POLLUTION:
                return self.nodes[index].get_min_expected_filter_state_index("pollution")
            case _:
                print(f"Algorithm couldn't update due to invalid Alg")
                return None

    def update(self):
        start_time = time.time()
        for index in range(self.nodes_size):
            if not self.nodes[index].prevent_state_change:
                self.nodes[index].prevent_state_change = True
                next_active_index = self.get_next_active_index(index)
                self.threads[index] = (threading.Thread(target=self.nodes[index].update_state, args=(next_active_index,)))
                self.threads[index].start()
        end_time = time.time()
        delta_time = end_time - start_time
        if delta_time < 0.1:
            time.sleep(0.1 - delta_time)

    def run(self):
        for node in self.nodes:
            active_index = random.randint(0, node.states_size - 1)
            node.set_traffic_lights_states(active_index)
        while not self.terminate_flag:
            self.update()
