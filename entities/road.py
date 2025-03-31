from entities.lane import Lane

class Road:
    def __init__(self, start_junction, end_junction, lanes=1):
        self.start = start_junction
        self.end = end_junction
        self.lanes = [Lane() for _ in range(lanes)]