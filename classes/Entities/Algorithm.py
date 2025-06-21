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
            threads.append(threading.Thread(target=self.nodes[index].update_state))
            threads[index].start()
        for index in range(self.nodes_size):
            threads[index].join()

    def update_green_wave(self):
        pass

    def update(self):
        match self.alg:
            case Alg.FIXED_TIMING_CYCLE:
                return self.update_fixed_timing_cycle()
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
