import random
import sys
import comms
from object_types import ObjectTypes

import math

class Game:
    """
    Stores all information about the game and manages the communication cycle.
    Available attributes after initialization will be:
    - tank_id: your tank id
    - objects: a dict of all objects on the map like {object-id: object-dict}.
    - width: the width of the map as a floating point number.
    - height: the height of the map as a floating point number.
    - current_turn_message: a copy of the message received this turn. It will be updated everytime `read_next_turn_data`
        is called and will be available to be used in `respond_to_turn` if needed.
    """
    def __init__(self):
        tank_id_message: dict = comms.read_message()
        self.tank_id = tank_id_message["message"]["your-tank-id"]
        self.enemy_tank_id = tank_id_message["message"]["enemy-tank-id"]

        self.current_turn_message = None

        # We will store all game objects here
        self.objects = {}

        # self.current_destination = [mid_x,mid_y] #TODO

        self.tick_counter = 0
        self.change_tick_count = 5
        self.waiting = False


        next_init_message = comms.read_message()
        while next_init_message != comms.END_INIT_SIGNAL:
            # At this stage, there won't be any "events" in the message. So we only care about the object_info.
            object_info: dict = next_init_message["message"]["updated_objects"]

            # Store them in the objects dict
            self.objects.update(object_info)

            # Read the next message
            next_init_message = comms.read_message()

        # We are outside the loop, which means we must've received the END_INIT signal

        # Let's figure out the map size based on the given boundaries

        # Read all the objects and find the boundary objects
        boundaries = []
        for game_object in self.objects.values():
            if game_object["type"] == ObjectTypes.BOUNDARY.value:
                boundaries.append(game_object)

        # The biggest X and the biggest Y among all Xs and Ys of boundaries must be the top right corner of the map.

        # Let's find them. This might seem complicated, but you will learn about its details in the tech workshop.
        biggest_x, biggest_y = [
            max([max(map(lambda single_position: single_position[i], boundary["position"])) for boundary in boundaries])
            for i in range(2)
        ]

        self.width = biggest_x
        self.height = biggest_y

    def read_next_turn_data(self):
        """
        It's our turn! Read what the game has sent us and update the game info.
        :returns True if the game continues, False if the end game signal is received and the bot should be terminated
        """
        # Read and save the message
        self.current_turn_message = comms.read_message()

        if self.current_turn_message == comms.END_SIGNAL:
            return False

        # Delete the objects that have been deleted
        # NOTE: You might want to do some additional logic here. For example check if a powerup you were moving towards
        # is already deleted, etc.
        for deleted_object_id in self.current_turn_message["message"]["deleted_objects"]:
            try:
                del self.objects[deleted_object_id]
            except KeyError:
                pass

        # Update your records of the new and updated objects in the game
        # NOTE: you might want to do some additional logic here. For example check if a new bullet has been shot or a
        # new powerup is now spawned, etc.
        self.objects.update(self.current_turn_message["message"]["updated_objects"])
        # print(self.objects , file=sys.stderr)

        return True


    def is_path_clear(self, path: list):
        for game_object in self.objects.values():
            if game_object["type"] == ObjectTypes.WALL.value and game_object["position"] in path:
                return False
        return True

    def calculate_distance(self, pos1, pos2):
        return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5

    def get_angle(self,enemy_tank_pos, our_tank_pos):
        dx = enemy_tank_pos[0] - our_tank_pos[0]
        dy = enemy_tank_pos[1] - our_tank_pos[1]
        return (math.degrees(math.atan2(dy, dx)) + 360) % 360

    # Swap between waiting and not waiting mode
    def swap_waiting(self, time: int = 2):
        self.waiting = not self.waiting
        self.tick_counter = 0
        self.change_tick_count = time if self.waiting else 5


    # Check if point is between tanks
    def is_between(self, point: list, tank1_pos: list, tank2_pos: list) -> bool:
        total = int(self.calculate_distance(tank1_pos, tank2_pos))
        dist = total - int((self.calculate_distance(point, tank1_pos) + self.calculate_distance(point, tank2_pos)))
        return dist == 0

        # for i in range(9):
        #     for j in range(9):
        #         dist = total - int((self.calculate_distance([point[0]+i, point[1]+j], tank1_pos) + self.calculate_distance([point[0]+i, point[1]+j], tank2_pos)))
        #         if dist == 0:
        #             return True
        #         dist = total - int((self.calculate_distance([point[0]+i, point[1]-j], tank1_pos) + self.calculate_distance([point[0]+i, point[1]-j], tank2_pos)))
        #         if dist == 0:
        #             return True

        #     for j in range(9):
        #         dist = total - int((self.calculate_distance([point[0]-i, point[1]+j], tank1_pos) + self.calculate_distance([point[0]-i, point[1]+j], tank2_pos)))
        #         if dist == 0:
        #             return True
        #         dist = total - int((self.calculate_distance([point[0]-i, point[1]-j], tank1_pos) + self.calculate_distance([point[0]-i, point[1]-j], tank2_pos)))
        #         if dist == 0:
        #             return True


    # check if tank is close to boundary
    def check_boundary(self,our_tank_pos,closing_boundary_pos):
        if abs(our_tank_pos[0]-closing_boundary_pos[0]) < 100  or abs(our_tank_pos[1]-closing_boundary_pos[1]) < 100:
            return True
        else:
            return False

    # get closing boundary position
    def get_closing_boundaries_positions(self):
        closing_boundaries = []
        for game_object in self.objects.values():
            if game_object["type"] == ObjectTypes.CLOSING_BOUNDARY.value:
                return game_object['position']

    def get_closest_boundary_pos(self,our_tank_pos):
        closing_boundaries = self.get_closing_boundaries_positions()
        print('passed - ',closing_boundaries[0],file=sys.stderr)
        # get the boundary to which the tank is closest
        bound = closing_boundaries[0]
        curr = abs(self.calculate_distance(our_tank_pos,closing_boundaries[0]))
        for boundary in closing_boundaries:
            if abs(self.calculate_distance(our_tank_pos,boundary)) < curr:
                curr = abs(self.calculate_distance(our_tank_pos,boundary))
                bound = boundary
        return bound

    def check_within_boundary(self, position):
        """Return True if the position is within the closing boundaries."""

        closing_boundaries = self.get_closing_boundaries_positions()
        if  (position[0] < closing_boundaries[0][0]) or \
            (position[0] < closing_boundaries[1][0]) or \
            (position[0] > closing_boundaries[2][0]) or \
            (position[0] > closing_boundaries[3][0]) or \
            (position[1] > closing_boundaries[0][1]) or \
            (position[1] < closing_boundaries[1][1]) or \
            (position[1] < closing_boundaries[2][1]) or \
            (position[1] > closing_boundaries[3][1]):
            return False
        else:
            return True

    def calculate_boundary(self):
        boundaries = [obj for obj in self.objects.values() if obj["type"] == ObjectTypes.CLOSING_BOUNDARY.value]
        if not boundaries:
            return None, None

        max_x = max(obj["position"][0][0] for obj in boundaries)
        max_y = max(obj["position"][0][1] for obj in boundaries)
        min_x = min(obj["position"][0][0] for obj in boundaries)
        min_y = min(obj["position"][0][1] for obj in boundaries)

        return (min_x, min_y), (max_x, max_y)

    def position_to_boundary(self, position):
        return self.calculate_distance(position, self.get_closest_boundary_pos(position))

    def is_reachable(self, position):
        player_velocity = 100
        boundary_velocity = 10

        player_to_position = self.calculate_distance(self.objects[self.tank_id]["position"], position)
        position_to_boundary = self.position_to_boundary(position)

        # time to reach the position
        time_for_player = player_to_position / player_velocity
        time_for_boundary = position_to_boundary / boundary_velocity

        return time_for_player < time_for_boundary

    def respond_to_turn(self):
        """
        This is where you should write your bot code to process the data and respond to the game.
        """
        message = {}

        # Get all walls
        walls = []
        for game_object in self.objects.values():
            if game_object["type"] == ObjectTypes.WALL.value:
                walls.append(game_object)

        # Get all breakable walls
        br_walls = []
        for game_object in self.objects.values():
            if game_object["type"] == ObjectTypes.DESTRUCTIBLE_WALL.value:
                br_walls.append(game_object)

        closing_boundaries = self.get_closing_boundaries_positions()
        # print(closing_boundaries,file=sys.stderr)

        # Get all power-ups
        powerups = []
        for game_object in self.objects.values():
            if game_object["type"] == ObjectTypes.POWERUP.value:
                powerups.append(game_object)
        for powerup in powerups:
            if not (self.check_within_boundary(powerup["position"]) and self.is_reachable(powerup["position"])):
                powerups.remove(powerup)
        print('powerups - ',powerups,file=sys.stderr)
        # print(powerups,file=sys.stderr)

        # Get our tank's position
        our_tank = self.objects[self.tank_id]
        our_tank_pos = our_tank["position"]

        # Get enemy tank's position
        enemy_tank = self.objects[self.enemy_tank_id]
        enemy_tank_pos = enemy_tank["position"]

        closing_boundary_pos = self.get_closest_boundary_pos(our_tank_pos)
        # print('boundary - ',closing_b,file=sys.stderr)
        # closing_boundary_pos = closing_b["position"]
        if self.check_boundary(our_tank_pos,closing_boundary_pos):
            new_angle = self.get_angle(closing_boundary_pos, our_tank_pos) + random.randint(165, 195)
            if new_angle > 360:
                new_angle = new_angle - 360
            
            cent_path = [870, 375]
            
            # for wall, br_wall in zip(walls, br_walls):
            #     while cent_path[1] in range(wall["position"][1], wall["position"][1] - 10) or \
            #         cent_path[1] in range(br_wall["position"][1], br_wall["position"][1] - 10):
            #         cent_path[1] -= 10
            
            message["path"] = cent_path
            message["shoot"] = self.get_angle(enemy_tank_pos, our_tank_pos)
            print("close to boundary",file=sys.stderr)
            self.swap_waiting(4)

        elif not self.waiting:
            # print(self.tick_counter, self.change_tick_count, file=sys.stderr)
            if self.tick_counter >= self.change_tick_count and not powerups:
                # print("here", file=sys.stderr)
                face_angle = self.get_angle(enemy_tank_pos, our_tank_pos)
                change_dir = random.choice((face_angle + 45, face_angle - 45))

                message["move"] = change_dir

                self.swap_waiting()


            elif powerups:
                # If there are power-ups, move towards the nearest one
                message["path"] = powerups[0]["position"]

            else:
                # If there are no power-ups, move towards the enemy tank and shoot at it
                if self.calculate_distance(our_tank_pos, enemy_tank_pos) > 100:
                    message["path"] = enemy_tank_pos

                else:
                    # If we are within a distance of 10 from the enemy, start circling around the enemy
                    # and predicting its position to shoot
                    next_angle = self.get_angle(enemy_tank_pos, our_tank_pos) + 180 + random.randint(-90, 90)
                    message["move"] = next_angle if next_angle < 360 else next_angle - 360
                    self.swap_waiting()
        else:
            # print(self.tick_counter, self.change_tick_count, file=sys.stderr)
            if self.tick_counter >= self.change_tick_count:
                # print("here2", file=sys.stderr)
                self.swap_waiting()

        self.tick_counter += 1

        safe_shoot = True
        for wall in walls:

            # print(wall, file=sys.stderr)
            if self.is_between(wall["position"], enemy_tank_pos, our_tank_pos):
                is_br_wall = False
                for br_wall in br_walls:
                    if self.is_between(br_wall["position"], our_tank_pos, wall["position"]):
                        is_br_wall = True
                        break
                # print("here3", file=sys.stderr)
                safe_shoot = is_br_wall
                break

        if safe_shoot: message["shoot"] = self.get_angle(enemy_tank_pos, our_tank_pos)

        comms.post_message(message)
