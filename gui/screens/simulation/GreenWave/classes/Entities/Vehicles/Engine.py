import random

class Engine:
    def __init__(self, max_acceleration, engine_type):
        self.max_acceleration = max_acceleration
        self.type = engine_type
        self.prefix = 0  # between -1 and 1. Used for determining the relative amount of force acting on the gas (between 0 and 1) or on the breaks (between -1 and 0)
        # TODO creating other needed fields

    # TODO writing the method
    def calculate_acceleration(self):
        self.prefix = random.randint(-100, 100) / 100
        return self.max_acceleration * self.prefix
