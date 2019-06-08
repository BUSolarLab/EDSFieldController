import requests
import json



def get_latlng():
    #Input user for their address
    street_name = input('Enter street name: ')
    city = input('Enter city name: ')
    state = input('Enter state/province: ')
    country = input('Enter country: ')

    #Assemble the address
    street_name.replace(" ", '+')
    loc = (street_name + ',+' + city + ',+' + state + ',+' + country)

    #Use mapquest API get request
    key = 'iaXKOTs032MKztwyRx0d9NB4HoWOF4Da'
    val = ('http://www.mapquestapi.com/geocoding/v1/address?key='+key+'&location='+loc)
    response = requests.get(val)
    result = response.json()

    #Get the latitude and longitude
    lat = result['results'][0]['locations'][0]['latLng']['lat']
    lng = result['results'][0]['locations'][0]['latLng']['lng']
    print('Latitude: ' + str(lat))
    print('Longitude: ' + str(lng))

    return (lat, lng)

'''
#Test code
(lat, lng) = get_latlng()
print(lat)
print(lng)
'''

'''
Format of the Get Request:
{'info': {'statuscode': 0, 'copyright': {'text': '© 2019 MapQuest, Inc.', 'imageUrl': 'http://api.mqcdn.com/res/mqlogo.gif', 'imageAltText': '© 2019 MapQuest, Inc.'}, 'messages': []}, 
'options': {'maxResults': -1, 'thumbMaps': True, 'ignoreLatLngInput': False}, 
'results': [{'providedLocation': {'location': 'Washington,DC'}, 'locations': [{'street': '', 'adminArea6': '', 'adminArea6Type': 'Neighborhood', 'adminArea5': 'Washington', 'adminArea5Type': 'City', 'adminArea4': 'District of Columbia', 'adminArea4Type': 'County', 'adminArea3': 'DC', 'adminArea3Type': 'State', 'adminArea1': 'US', 'adminArea1Type': 'Country', 'postalCode': '', 'geocodeQualityCode': 'A5XAX', 'geocodeQuality': 'CITY', 'dragPoint': False, 'sideOfStreet': 'N', 'linkId': '282772166', 'unknownInput': '', 'type': 's', 'latLng': {'lat': 38.892062, 'lng': -77.019912}, 'displayLatLng': {'lat': 38.892062, 'lng': -77.019912}, 'mapUrl': 'http://www.mapquestapi.com/staticmap/v5/map?key=iaXKOTs032MKztwyRx0d9NB4HoWOF4Da&type=map&size=225,160&locations=38.892062,-77.019912|marker-sm-50318A-1&scalebar=true&zoom=12&rand=-525298491'}]}]}

Format of the address example
"1600 Amphitheatre Parkway, Mountain View, CA"
address=1600+Amphitheatre+Parkway,+Mountain+View,+CA
'''