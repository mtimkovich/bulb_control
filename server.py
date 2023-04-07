import bulbs
import json
import logging
import os.path
from flask import Flask, request
from flask_caching import Cache
from wyze_sdk import Client
from wyze_sdk.errors import WyzeApiError

def get_token(cache):
    if os.path.exists('tokens.json'):
        with open('tokens.json') as f:
            data = json.load(f)
            token = data['access_token']
            refresh_token = data['refresh_token']
        client = Client(token=token, refresh_token=refresh_token)
    else:
        with open('credentials.json') as fp:
            cred = json.load(fp)
        response = Client().login(
            email=cred['email'],
            password=cred['password']
        )

        client = Client(token=response['access_token'])

    cache.set('client', client)

def write_tokens(client, filename):
    with open('tokens.json', 'w') as f:
        data = {
            'access_token': client._token,
            'refresh_token': client._refresh_token
        }

        json.dump(data, f)

def get_client(cache):
    client = cache.get('client')
    try:
        client.user_get_info()
    except WyzeApiError as e:
        if 'refresh the token' in str(e):
            logging.info('refreshing auth token')
            client.refresh_token()
            write_tokens(client, 'tokens.json')
            cache.set('client', client)
        else:
            raise e
    return client

def create_app():
    cache = Cache(config={
        'CACHE_TYPE': 'SimpleCache',
    })
    app = Flask(__name__)
    cache.init_app(app)

    get_token(cache)

    @app.route('/')
    def hello_world():
        # TODO: load the bootstrap page
        return 'hello, world'

    @app.route('/load', methods=['POST'])
    def load():
        name = request.form.get('name')

        if name is None:
            return 'name is not set', 400

        client = get_client(cache)

        try:
            bulbs.load_state(client, name)
        except KeyError as e:
            return str(e), 400

        return f'Set {name} lights', 200

    return app
