import bulbs
import json
import logging
import os.path
from flask import Flask, request, render_template
from flask_caching import Cache
from wyze_sdk import Client
from wyze_sdk.errors import WyzeApiError

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
        'CACHE_DEFAULT_TIMEOUT': 0,
    })
    app = Flask(__name__)
    cache.init_app(app)

    cache.set('client', bulbs.create_client())

    @app.route('/')
    def index():
        return render_template('index.html')

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
