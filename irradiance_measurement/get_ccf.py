import requests
import json
from get_coordinates import get_latlng

#Get the coordinates from current address
(lat, lng) = get_latlng()


def get_CCF(lat,lng):
    #Use mapquest API get request
    key = 'af27ec1d49d75248c9e71512090c1e0f'
    val = ('https://api.darksky.net/forecast/'+key+'/'+str(lat)+','+str(lng))
    response = requests.get(val)
    result = response.json()
    currentData = result['currently']
    minuteData = result['minutely']
    hourData = result['hourly']
    dailyData = result['daily']

    #Get relevant parameters
    summary = currentData['summary']
    ccf = currentData['cloudCover']
    icon = currentData['icon']
    print('Summary: ' + summary + '\n' + 'Icon: ' + icon + '\n' + 'Cloud Cover Factor: ' + str(ccf) + '\n')
    
    return ccf

get_CCF(lat, lng)

'''
Sample get request format:
https://api.darksky.net/forecast/af27ec1d49d75248c9e71512090c1e0f/37.8267,-122.4233


Sample get request documentation
https://darksky.net/dev/docs#overview

'''