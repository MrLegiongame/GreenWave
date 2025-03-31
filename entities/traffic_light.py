class TrafficLight:
    def __init__(self):
        self.state = "green"
        self.timer = 0
        self.cycle = ["green", "yellow", "red"]

    def update(self):
        self.timer += 1
        if self.timer % 5 == 0:
            current_index = self.cycle.index(self.state)
            self.state = self.cycle[(current_index + 1) % len(self.cycle)]
        print(f"Traffic light state: {self.state}")