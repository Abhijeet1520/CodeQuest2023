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


    def get_object_by_type(self, object_type: int):
        return {k: v for k, v in self.objects.items() if v['type'] == object_type}

    def get_distance(self, object1: dict, object2: dict):
        x1, y1 = object1['position']
        x2, y2 = object2['position']
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

    def get_direction(self, object1: dict, object2: dict):
        x1, y1 = object1['position']
        x2, y2 = object2['position']
        return math.degrees(math.atan2(y2 - y1, x2 - x1)) % 360

    def move_towards(self, target: dict):
        direction = self.get_direction(self.objects[self.tank_id], target)
        return [direction, 100]  # Move 100 units in the direction of the target

    def shoot_at(self, target: dict):
        return self.get_direction(self.objects[self.tank_id], target)



    def get_nearest_object(self, object_type: int):
        tank = self.objects[self.tank_id]
        objects_of_type = self.get_object_by_type(object_type)
        distances = {k: self.get_distance(tank, v) for k, v in objects_of_type.items()}
        return min(distances, key=distances.get)

    def is_path_clear(self, path: list):
        for game_object in self.objects.values():
            if game_object["type"] == ObjectTypes.WALL.value and game_object["position"] in path:
                return False
        return True

    def get_surrounding_objects(self, radius: int):
        tank = self.objects[self.tank_id]
        return {k: v for k, v in self.objects.items() if self.get_distance(tank, v) <= radius}
 
    # def get_closest_enemy(self):
    #     enemies = [obj for obj in self.objects.values() if obj["type"] == ObjectTypes.TANK.value and obj["id"] != self.tank_id]
    #     if not enemies:
    #         return None

    #     my_tank = self.objects[self.tank_id]
    #     my_position = my_tank["position"]

    #     closest_enemy = min(enemies, key=lambda e: self.calculate_distance(my_position, e["position"]))
    #     return closest_enemy

    def calculate_distance(self, pos1, pos2):
        return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5

    def get_angle(self,enemy_tank_pos, our_tank_pos):
        dx = enemy_tank_pos[0] - our_tank_pos[0]
        dy = enemy_tank_pos[1] - our_tank_pos[1]
        return math.degrees(math.atan2(dy, dx))
    

    # Swap between waiting and not waiting mode
    def swap_waiting(self):
        self.waiting = not self.waiting
        self.tick_counter = 0
        self.change_tick_count = 2 if self.waiting else 5

    
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

    def get_closest_boundary(self,our_tank_pos,closing_boundaries):
        print('passed - ',closing_boundaries[0][0],file=sys.stderr)
        # get the boundary to which the tank is closest
        bound = closing_boundaries[0][0]
        curr = abs(self.calculate_distance(our_tank_pos,closing_boundaries[0][0]))
        for boundary in closing_boundaries[0]:
            if abs(self.calculate_distance(our_tank_pos,boundary)) < curr:
                curr = abs(self.calculate_distance(our_tank_pos,boundary))
                bound = boundary
        return bound
    
    
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

        # get closing boundary position
        closing_boundaries = []
        for game_object in self.objects.values():
            if game_object["type"] == ObjectTypes.CLOSING_BOUNDARY.value:
                closing_boundaries.append(game_object['position'])
        print(closing_boundaries,file=sys.stderr)

        # Get all power-ups
        powerups = []
        for game_object in self.objects.values():
            if game_object["type"] == ObjectTypes.POWERUP.value:
                powerups.append(game_object)
        # print(powerups,file=sys.stderr)

        # Get our tank's position
        our_tank = self.objects[self.tank_id]
        our_tank_pos = our_tank["position"]

        # Get enemy tank's position
        enemy_tank = self.objects[self.enemy_tank_id]
        enemy_tank_pos = enemy_tank["position"]

        closing_boundary_pos = self.get_closest_boundary(our_tank_pos,closing_boundaries)
        # print('boundary - ',closing_b,file=sys.stderr)
        # closing_boundary_pos = closing_b["position"]
        if self.check_boundary(our_tank_pos,closing_boundary_pos):
            new_angle = self.get_angle(closing_boundary_pos, our_tank_pos) + random.randint(165, 195)
            if new_angle > 360:
                new_angle = new_angle - 360
            message["move"] = new_angle
            message["shoot"] = self.get_angle(enemy_tank_pos, our_tank_pos)
            print("close to boundary",file=sys.stderr)

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
                # nearest_power_up_id = self.get_nearest_object(ObjectTypes.POWERUP.value)
                nearest_power_up = powerups[0]["position"]
                message["path"] = nearest_power_up                

                # # If the path to the power-up is clear, move towards it
                # if self.is_path_clear(nearest_power_up):
                #     comms.post_message({
                #         "path": nearest_power_up
                #     })
                # else:
                #     # If the path is not clear, find the nearest TANK and shoot at it
                #     nearest_wall_id = self.get_nearest_object(ObjectTypes.TANK.value)
                #     nearest_wall = self.objects[nearest_wall_id]
                #     comms.post_message({
                #         "path": nearest_power_up,
                #         "shoot": self.shoot_at(nearest_wall)
                #     })
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
                # print("here3", file=sys.stderr)
                safe_shoot = False
                break

        if safe_shoot: message["shoot"] = self.get_angle(enemy_tank_pos, our_tank_pos)

        comms.post_message(message)