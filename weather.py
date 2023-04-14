# TODO: This will eventually be used to adjust the lights when it's cloudy.
import requests

api_url = 'https://api.weather.gov/gridpoints/SEW/125,70/forecast'

def is_cloudy():
    data = requests.get(api_url).json()
    weather = data['properties']['periods'][0]
    # print(weather)
    forecast = weather['detailedForecast'].lower()

    print(forecast)
    print('cloudy' in forecast)
    return 'cloudy' in forecast

if __name__ == '__main__':
    is_cloudy()
