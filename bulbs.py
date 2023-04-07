#!/usr/bin/env python
from functools import partial
from multiprocessing import Pool
from wyze_sdk import Client
from wyze_sdk.errors import WyzeApiError
import json
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
        self.client.bulbs.set_color(device_mac=self.mac,
                                    device_model=self.model,
                                    color=state['color'])
        self.client.bulbs.set_color_temp(device_mac=self.mac,
                                         device_model=self.model,
                                         color_temp=state['color_temp'])
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

def save_state(bulbs, filename):
    filename += '.json'
    # TODO: Check if scene already exists and prompt for override.
    state = []
    for bulb in bulbs:
        # TODO: Parellelize this
        bulb.get_info()
        state.append(bulb.to_dict())
    with open(os.path.join('scenes', filename), 'w') as fp:
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
    if len(sys.argv) < 2:
        print('load or save')
        sys.exit(1)

    client = create_client()

    try:
        if sys.argv[1] == 'save':
            print('hello')
            bulbs = filter_bulbs(client)
            save_state(bulbs, filename)
        elif sys.argv[1] == 'load':
            load_state(client, filename)
        else:
            print(f'Unrecognized command {sys.argv[1]}')
            sys.exit(1)

    except WyzeApiError as e:
        print(e)
