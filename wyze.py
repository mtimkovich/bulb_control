import json
from multiprocessing import Pool
import os
import sys
from wyze_sdk import Client
from wyze_sdk.errors import WyzeApiError

def get_token():
    with open('credentials.json') as fp:
        cred = json.load(fp)
    response = Client().login(
        email=cred['email'],
        password=cred['password']
    )

    with open('token.txt', 'w') as f:
        f.write(response['access_token'])

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
        self.client.bulbs.set_brightness(device_mac=self.mac, device_model=self.model, brightness=state['brightness'])
        self.client.bulbs.set_color(device_mac=self.mac, device_model=self.model, color=state['color'])
        self.client.bulbs.set_color_temp(device_mac=self.mac, device_model=self.model, color_temp=state['color_temp'])

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

def _set_bulb_fn(state):
    bulb = bulb_from_nickname(client, state['nickname'])
    bulb.set_values(state)

def set_bulb(client):
    return _set_bulb_fn

def save_state(bulbs, filename):
    state = []
    for bulb in bulbs:
        bulb.get_info()
        state.append(bulb.to_dict())
    with open(os.path.join('scenes', filename), 'w') as fp:
        json.dump(state, fp, sort_keys=True, indent=2)

def load_state(client, filename):
    try:
        with open(os.path.join('scenes', filename)) as fp:
            states = json.load(fp)
    except FileNotFoundError:
        print(f'No scene named {filename}')
        return
    with Pool(20) as p:
        p.map(set_bulb(client), states)
    # for state in states:
    #     (set_bulb(client))(state)

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
        print('auth, load, or save')
        sys.exit(1)

    if sys.argv[1] == 'auth':
        get_token()
        sys.exit()

    with open('token.txt') as f:
        token = f.read()

    client = Client(token=token)

    try:
        filename = f'{sys.argv[2]}.json'

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
