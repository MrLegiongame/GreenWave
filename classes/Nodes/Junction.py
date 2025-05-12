from classes.Entities.Point import Point
from classes.Nodes.Direction import Direction
from screens.functions import create_state_from_flow, create_flow_with_lanes_group


def check_junction_validity(directions):  # directions: tuple[Direction]
    """
    Checks whether the values are valid (e.g. no future overflows nor possible collisions)
    each lane in a certain direction is sorted from right (index 0) to left (index len(direction) - 1)
    """
    if not isinstance(directions, list):
        raise TypeError("Junction is invalid: Not a tuple parameter was given")
    size = 0
    for direction in directions:
        if not isinstance(direction, Direction):
            raise TypeError("Junction is invalid: Non-Direction value")
        size += 1
    if not (size >= 2):
        raise TypeError("Junction is invalid: Not enough directions")
    return True


class Junction:

    """
    We assume each Junction's inside (of size n; directions) is circular, which means that inside[0] is next to
    both inside[n-1] and inside[1]. The same goes for inside[k] (0<k<n-1) which is next to
    both inside[k-1] and inside[k+1].
    The variable 'outside' stores how many lanes are in each direction's outside side from the junction.
    We assume that the indexes are sorted counter-clockwise relatively to the Junction's directions.
    """

    def __init__(self, directions=None):  # directions: list[Direction]
        self.directions = []
        self.size = 0
        self.cur_state = None
        self.available_states = None
        self.states_size = None
        self.point = None

        self.distance = None  # for bfs use only
        self.source_junction = None # for bfs use only

        if None is not directions:
            try:
                check_junction_validity(directions)
                self.directions = directions
                self.size = len(directions)
                self.__set_junction()
                self.__set_lanes_as_direction_tuple()
                self.available_states = self.create_states()  # tuple[tuple[Lane]]
                self.states_size = len(self.available_states)
            except TypeError as e:
                print(f"Junction couldn't be created due to this error: {e}")

    def __set_junction(self):
        for direction in self.directions:
            direction.set_parent_junction(self)

    def __set_lanes_as_direction_tuple(self):
        for direction in range(self.size):
            for lane in range(self.directions[direction].size):
                new_lane, index = [None] * self.directions[direction].direction[lane].size, 0
                for to_direction in self.directions[direction].direction[lane].lane:
                    new_lane[index] = self.directions[(to_direction + direction + 1) % self.size]
                    index += 1
                self.directions[direction].set_lane_as_direction_tuple(tuple(new_lane), lane)

    def set_point(self, point):
        if isinstance(point, Point):
            self.point = point

    def add_direction(self, direction):
        if isinstance(direction, Direction):
            self.directions.append(direction)
            self.size += 1
            """
            self.available_states = self.create_states()  # tuple[tuple[Lane]]
            self.states_size = len(self.available_states)
            """

    def get_neighbors_junctions(self):
        neighbors = []
        for direction in self.directions:
            edge = direction.road
            neighbor = edge.first_direction.parent_junction
            if self is neighbor:
                neighbor = edge.second_direction.parent_junction
            neighbors.append([neighbor, edge])
        return neighbors

    def get_road_by_neighbor(self, junction):
        for direction in self.directions:
            neighbor = direction.road.first_direction.parent_junction
            if self is neighbor:
                neighbor = direction.road.second_direction.parent_junction
            if junction is neighbor:
                return direction.road
        return None

    def remove_direction(self, direction):
        for direction_index in range(self.directions):
            if self.directions[direction_index] is direction:
                self.directions.pop(direction_index)
                self.size -= 1
                """
                self.available_states = self.create_states()  # tuple[tuple[Lane]]
                self.states_size = len(self.available_states)
                """

    def get_in_lanes_groups(self):
        res = set()
        lanes_group = set()

        for direction in self.directions:
            lanes_group = set()
            directions_group = set()
            for lane in direction.in_lanes:
                if 0 == len(directions_group):
                    lanes_group.add(lane)
                    directions_group.update(to_lane.parent_junction for to_lane in lane.to_lanes)
                else:
                    directions_check_group = set()
                    directions_check_group.update(to_lane.parent_junction for to_lane in lane.to_lanes)
                    if not (directions_check_group & directions_group):  # if the intersection of the sets is empty
                        res.add(lanes_group)
                        lanes_group.clear()
                        lanes_group.add(lane)
                        directions_group = directions_check_group
                    else:
                        lanes_group.add(lane)
                        directions_group = directions_check_group | directions_group  # updates the group to be the union of both of them

        res.add(lanes_group)
        return res

    def create_states(self):
        states = set()
        if not self.size >= 2:
            return None

        for lanes_group in self.get_in_lanes_groups():
            state = create_state_from_flow(create_flow_with_lanes_group(self, lanes_group))
            states.add(state)

        return states

    def set_states(self):
        self.available_states = self.create_states()
        self.states_size = len(self.available_states)

    def __str__(self):
        res = f"Junction has {self.size} directions:\n\n"
        for direction in self.directions:
            res += f"\t{direction}\n"
        return res
