import paho.mqtt.client as mqtt
import time
import pickle
import threading
import timeit
import pygame
import numpy as np
import pickle
import sys
import os


class Player(pygame.sprite.Sprite):
    def __init__(self, name, sprite):
        super().__init__()

        #player
        self.name = name
        player_sprite = pygame.image.load(sprite).convert_alpha()
        self.player_sprite =  pygame.transform.scale(player_sprite, (70, 70))
        self.player_rect = self.player_sprite.get_rect(center = (35, 35))
        self.player_rotation = 0
        player_death_sprite = pygame.image.load('paho_mqtt/sprites/death.png').convert_alpha()
        self.player_death_sprite =  pygame.transform.scale(player_death_sprite, (70, 70))

        #shoot
        shoot_sprite = pygame.image.load('paho_mqtt/sprites/orb0.png').convert_alpha()
        self.shoot_sprite =  pygame.transform.scale(shoot_sprite, (20, 20))
        self.shoot_rect_list = []

    def update(self, player_rect, player_rotation, shoot_rect_list, is_dead):
        if is_dead:
            self.player_sprite = self.player_death_sprite
        
        self.player_rotation = player_rotation
        self.player_rect = player_rect
        self.shoot_rect_list = shoot_rect_list


class Players(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.max_players = 4 
        self.players_dict = {}

    def create_player(self, name, skin):
        new_player = Player(
            name=name,
            sprite=skin,
        )
        self.players_dict[name] = new_player

    def __len__(self):
        return len(self.players_dict)

def screen_update():
    global players

    FPS_input = 60
    FPS_screen = 60

    real_FPS_screen = 60
    real_FPS_input = 60

    while True:
        t0 = timeit.default_timer()

        FPS_screen_text = font.render(f'FPS (Tela) : {FPS_screen} - {real_FPS_screen:.0f}', False, 'black')
        FPS_input_text = font.render(f'FPS (Input): {FPS_input} - {real_FPS_input:.0f}', False, 'black')

        screen.blit(map_background, (0,0))
    
        for player in players.players_dict:
            #print(players.players_dict[player].player_rotation)
            screen.blit(
                 pygame.transform.rotate(
                    players.players_dict[player].player_sprite,
                    players.players_dict[player].player_rotation - 90
                 ),
                players.players_dict[player].player_rect
            )

            for shoot_rect in players.players_dict[player].shoot_rect_list:
                screen.blit(
                    players.players_dict[player].shoot_sprite,
                    shoot_rect
                )

        screen.blit(FPS_screen_text, (10,10))
        screen.blit(FPS_input_text, (10,40))
        
        pygame.display.update()

        clock.tick(FPS_screen)
        real_FPS_screen = 1/(timeit.default_timer() - t0)


def bot_movement(player_name, cont, length, directions):
    t0 = timeit.default_timer()

    if cont >= length - 1: cont = 0
    else: cont += 1

    random_shoot = np.random.randint(0,360)
    inputs_dict = {
        'player_name': player_name,
        'player_skin': player_skin,
        'player_direction': directions[cont // (length//4)],
        'shoot_angle': random_shoot,
        'mouse_direction': random_shoot,
    }
    return cont, inputs_dict

def player_inputs(player_name):
    global players

    mouse_direction = players.players_dict[player_name].player_rotation
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEMOTION:
            mouse_coords = pygame.mouse.get_pos()
            player_position = players.players_dict[player_name].player_rect
            mouse_direction = -np.arctan2(
                mouse_coords[1] - player_position.y,
                mouse_coords[0] - player_position.x
                ) * 180 / np.pi


    click_direction = None
    if pygame.mouse.get_pressed()[0]:
        mouse_click_position = pygame.mouse.get_pos()
        player_position = players.players_dict[player_name].player_rect
        click_direction = mouse_direction
    
    keys = pygame.key.get_pressed()

    move_direction = np.array([0, 0])

    player_movement_dict = {
        'w': np.array([0,-1]),
        'a': np.array([-1,0]),
        's': np.array([0,+1]),
        'd': np.array([+1,0]),
    }

    if keys[pygame.K_w]:
        move_direction += player_movement_dict['w']
    if keys[pygame.K_a]:
        move_direction += player_movement_dict['a']
    if keys[pygame.K_s]:
        move_direction += player_movement_dict['s']
    if keys[pygame.K_d]:
        move_direction += player_movement_dict['d']

    inputs_dict = {
        'player_name': player_name,
        'player_skin': player_skin,
        'player_direction': move_direction,
        'shoot_angle': click_direction,
        'mouse_direction': mouse_direction,
    }

    return inputs_dict

def send_data(player_name, client):
    global players
    cont = 0
    while True:
        if 'bot' in player_name.lower():
            cont, inputs_dict = bot_movement(
                player_name=player_name,
                cont=cont,
                length=300, 
                directions=np.array([[1,0],[0,1],[-1,0],[0,-1]])
            )

        else:
            inputs_dict = player_inputs(player_name)
        
        client.publish('server_receive', pickle.dumps(inputs_dict))

        time.sleep(1/60)
        


def receive_data(client, userdata, message):
    global players
    all_players_data = pickle.loads(message.payload)
    #print(all_players_data)
    #try:
    for player_name in all_players_data:
        if player_name not in players.players_dict:
            #print(all_players_data[player_name])
            players.create_player(player_name, all_players_data[player_name]['player_skin'])
        else:
            #print('UPDATAR______*********')
            #players.players_dict = all_players_data[player_name]
            player_data = all_players_data[player_name]
            players.players_dict[player_name].update(
                player_data['player_rect'],
                player_data['player_rotation'],
                player_data['shoot_rect_list'],
                player_data['is_dead'],
            )

            #print(all_players_data[player_name]['player_skin'])


    #except: 
        #print('Erro no recebimento dos jogadores')
        


if __name__ == '__main__':

    os.system('cls')

    pygame.init()
    resX, resY = 1000, 600

    screen = pygame.display.set_mode((resX,resY))
    map_background = pygame.image.load('paho_mqtt/map/space2.png').convert_alpha()
    map_background = pygame.transform.scale(map_background, (resX, resY))
    font = pygame.font.Font(None, 35)

    pygame.display.set_caption('Pygame')
    clock = pygame.time.Clock()

    file_name = os.path.basename(__file__).replace('.py', '').rsplit('_', 1)

    player_name = file_name[0]
    player_skin = f'paho_mqtt/sprites/{file_name[1]}.png'

    mqtt_broker = '127.0.0.1'
    client = mqtt.Client(player_name)
    client.connect(mqtt_broker)

    client.loop_start()
    client.subscribe('server_send')

    time.sleep(0.1)

    players = Players()
    players.create_player(player_name, player_skin)

    client.on_message = receive_data

    #threading.Thread(target=send_data, args=(player_name, client,)).start()
    threading.Thread(target=screen_update).start()

    send_data(player_name, client)

    time.sleep(30)
    client.loop_forever