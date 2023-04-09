#!/usr/bin/env python
from colors import colors
from functools import partial
from multiprocessing import Pool
from wyze_sdk import Client
from wyze_sdk.errors import WyzeApiError
import json
import logging
import os
import sys

def create_client():
    if os.path.exists('tokens.json'):
        with open('tokens.json') as f:
            data = json.load(f)
            token = data['access_token']
            refresh_token = data['refresh_token']
        return Client(token=token, refresh_token=refresh_token)

    with open('credentials.json') as fp:
        cred = json.load(fp)
    response = Client().login(
        email=cred['email'],
        password=cred['password']
    )

    return Client(token=response['access_token'])

def write_tokens(client, filename):
    with open('tokens.json', 'w') as f:
        data = {
            'access_token': client._token,
            'refresh_token': client._refresh_token
        }

        json.dump(data, f)

def update_token(client):
    """Return if the token was updated."""
    try:
        client.user_get_info()
    except WyzeApiError as e:
        if 'refresh the token' in str(e):
            logging.info('refreshing auth token')
            client.refresh_token()
            write_tokens(client, 'tokens.json')
            return True
        else:
            raise e
    return False

class Bulb:
    def __init__(self, client, bulb):
        self.client = client

        self.nickname = bulb.nickname
        self.mac = bulb.mac
        self.model = bulb.product.model

        self.info = None

    def get_info(self):
        self.info = self.client.bulbs.info(device_mac=self.mac)
        self.brightness = self.info.brightness
        self.color = self.info.color
        self.color_temp = self.info.color_temp
        self.is_on = self.info.is_on

    def turn_on(self):
        self.client.bulbs.turn_on(device_mac=self.mac, device_model=self.model)

    def turn_off(self):
        self.client.bulbs.turn_off(device_mac=self.mac, device_model=self.model)

    def set_values(self, state):
        if not state['is_on']:
            self.turn_off()
            return

        self.turn_on()

        if 'color_name' in state:
            color = colors[state['color_name']]['color']
            color_temp = colors[state['color_name']]['color_temp']
        else:
            color = state['color']
            color_temp = state['color_temp']

        self.client.bulbs.set_color(device_mac=self.mac,
                                    device_model=self.model,
                                    color=color)
        self.client.bulbs.set_color_temp(device_mac=self.mac,
                                         device_model=self.model,
                                         color_temp=color_temp)
        self.client.bulbs.set_brightness(device_mac=self.mac,
                                         device_model=self.model,
                                         brightness=state['brightness'])

    def to_dict(self):
        return {
            'nickname': self.nickname,
            'is_on': self.is_on,
            'brightness': self.brightness,
            'color': self.color,
            'color_temp': self.color_temp
        }

    def __repr__(self):
        return str(self.to_dict())

def confirm(message):
    r = input(f'{message} [Y/n] ').lower()
    return r == 'y' or r == 'yes'

def info_dict(bulb):
    bulb.get_info()
    return bulb.to_dict()

def save_state(bulbs, filename):
    filename += '.json'
    scene_file = os.path.join('scenes', filename)

    if (os.path.exists(scene_file) and
        not confirm(f'{filename} already exists, override?')):
            return

    with Pool(20) as p:
        state = p.map(info_dict, bulbs)
    with open(scene_file, 'w') as fp:
        json.dump(state, fp, sort_keys=True, indent=2)

def set_bulb(client, state):
    bulb = bulb_from_nickname(client, state['nickname'])
    bulb.set_values(state)

def load_state(client, filename):
    filename += '.json'
    try:
        with open(os.path.join('scenes', filename)) as fp:
            states = json.load(fp)
    except FileNotFoundError:
        raise KeyError(f'No scene named {filename}')
    with Pool(20) as p:
        p.map(partial(set_bulb, client), states)

def filter_bulbs(client, prefix=''):
    """Return bulbs whose name start with @prefix."""
    for bulb in client.bulbs.list():
        if bulb.nickname.startswith(prefix):
            yield Bulb(client, bulb)

def bulb_from_nickname(client, name):
    for bulb in client.bulbs.list():
        if bulb.nickname == name:
            return Bulb(client, bulb)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('load or save')
        sys.exit(1)

    client = create_client()
    update_token(client)
    filename = sys.argv[2]

    try:
        if sys.argv[1] == 'save':
            bulbs = filter_bulbs(client)
            save_state(bulbs, filename)
        elif sys.argv[1] == 'load':
            load_state(client, filename)
        else:
            print(f'Unrecognized command {sys.argv[1]}')
            sys.exit(1)

    except WyzeApiError as e:
        print(e)
