import paho.mqtt.client as mqtt
import threading
import pygame
import timeit
import time
import pickle
import numpy as np
import os

os.system('cls')

class Player(pygame.sprite.Sprite):
    def __init__(self, name, skin):
        super().__init__()

        #player
        self.player_name = name
        self.player_skin = skin
        self.player_rotation = 0
        self.is_dead = False
        self.player_sprite = pygame.Surface((70, 70))
        self.player_rect = self.player_sprite.get_rect(center=(0, 0))
        self.player_speed = 5

        #shoot
        self.shoot_not_clicked = True
        self.shoot_sprite = pygame.Surface((50, 50))
        self.shoot_rect = self.shoot_sprite.get_rect(center=(25, 25))
        self.shoot_direction_list = [] # [(direction, rect), ...]
        self.shoot_rect_list = []
        self.shoot_speed = 8
        self.shoot_reload_time = 1
        self.shoot_max_shoots = 2

    def shoot(self, shoot_angle):
        if shoot_angle is None:
            return
        
        self.shoot_not_clicked = False

        if len(self.shoot_rect_list) >= self.shoot_max_shoots:
            del self.shoot_direction_list[0]
            del self.shoot_rect_list[0]

        rect_copy = self.player_rect.copy()
        x = rect_copy.x
        y = rect_copy.y
        x_inc = +np.cos(np.deg2rad(shoot_angle)) * self.shoot_speed
        y_inc = -np.sin(np.deg2rad(shoot_angle)) * self.shoot_speed
        
        self.shoot_direction_list.append(np.array([[x, y], [x_inc, y_inc]]))
        self.shoot_rect_list.append(rect_copy)

        time.sleep(self.shoot_reload_time)

        self.shoot_not_clicked = True


    def update(self, player_direction, shoot_angle, mouse_direction):
        global resX, resY

        # if self.is_dead:
        #     return

        if self.player_rect.x > resX:
            self.player_rect.x = resX
        elif self.player_rect.x < 0:
            self.player_rect.x = 0
        else:
            self.player_rect.x += player_direction[0] * self.player_speed

        if self.player_rect.y > resY:
            self.player_rect.y = resY
        elif self.player_rect.y < 0:
            self.player_rect.y = 0
        else:
            self.player_rect.y += player_direction[1] * self.player_speed

        self.player_rotation = mouse_direction

        if self.shoot_not_clicked:
            threading.Thread(
                target=self.shoot, 
                args=(shoot_angle,)
            ).start()
        
        valid_shoot_rect_list = []
        valid_shoot_direction_list = []
        for shoot_rect, shoot_direction in zip(
            self.shoot_rect_list, self.shoot_direction_list
            ):

            if abs(shoot_rect.x) < resX*2 and abs(shoot_rect.y) < resY*2:
                shoot_direction[0] += shoot_direction[1]
                shoot_rect.x = shoot_direction[0, 0]
                shoot_rect.y = shoot_direction[0, 1]

                valid_shoot_rect_list.append(shoot_rect)
                valid_shoot_direction_list.append(shoot_direction)
        
        self.shoot_rect_list = valid_shoot_rect_list
        self.shoot_direction_list = valid_shoot_direction_list

    def status(self):
        return {
            'player_skin': self.player_skin,
            'player_rect': self.player_rect,
            'player_rotation': self.player_rotation,
            'shoot_rect_list': self.shoot_rect_list,
            'is_dead': self.is_dead,
        }


class Players():
    def __init__(self):
        self.max_players = 4
        self.players_dict = {}

    def __len__(self):
        return len(self.players_dict)

    def create_player(self, name, skin):
        new_player = Player(
            name=name,
            skin=skin,
        )
        self.players_dict[name] = new_player

    def death(self):
        for player in self.players_dict:
            all_shoots = sum([
                self.players_dict[p].shoot_rect_list 
                for p in self.players_dict
                if self.players_dict[p].player_name != player
            ], [])

            if self.players_dict[player].player_rect.collidelist(all_shoots) > 0:
                self.players_dict[player].is_dead = True
                self.players_dict[player].shoot_rect_list = []
        
    def update_client(self):
        players_status = {}
        self.death()

        death_count = 0
        for player in self.players_dict:
            players_status[player] = self.players_dict[player].status()
            #print(players_status[player])
            if players_status[player]['is_dead']:
                death_count += 1
            else:
                player_alive = player

        if death_count == len(self.players_dict) - 1:
            for player in self.players_dict:
                self.players_dict[player].is_dead = False
            print(f'O jogador {player_alive} ganhou!')

        return players_status


def receive_data(client, userdata, message):
    global players

    data = pickle.loads(message.payload)

    if data['player_name'] not in players.players_dict:
        if len(players) < 4:
            players.create_player(data['player_name'], data['player_skin'])
        else: pass

    player = players.players_dict[data['player_name']]
    if not player.is_dead:
        player.update(
            data['player_direction'], 
            data['shoot_angle'],
            data['mouse_direction']
        )


def send_data(SERVER_TICK_RATE, client):
    clock = pygame.time.Clock()

    while True: 
        global players
        status = players.update_client()
        #print(status)
        try:    
            #print(status['cliente_2']['shoot_rect_list'])
            #print(status)
            client.publish('server_send', pickle.dumps(status))
        except:
            print('Erro ao enviar')

        #print('--------------')

        #time.sleep(0.5)
        clock.tick(SERVER_TICK_RATE)


if __name__ == '__main__':

    os.system('cls')

    mqtt_broker = 'mqtt.eclipseprojects.io'#'127.0.0.1'
    client = mqtt.Client('server_name')
    client.connect(mqtt_broker)

    resX, resY = 1000, 600
    SERVER_TICK_RATE = 60

    client.loop_start()
    client.subscribe('server_receive')

    players = Players()
    client.on_message = receive_data

    time.sleep(0.5)
    threading.Thread(target=send_data, args=(SERVER_TICK_RATE, client)).start()

    time.sleep(30)
    client.loop_forever