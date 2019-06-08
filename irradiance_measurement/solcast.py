import requests
import json

#Solcast API Information
key = 'aaaaaa' #Ask me for the key
url = 'https://api.solcast.com.au/weather_sites/ccdc-a235-f8ca-0884/estimated_actuals?format=json&api_key='+ key
response = requests.get(url)
result = response.json()

#Forecasted Estimates Parameters
ghi = result['estimated_actuals'][0]['ghi'] #Global Horizontal Irradiance Center Value (W/m2)
ebh = result['estimated_actuals'][0]['ebh'] #Direct (Beam) Horizontal Irradiance
dni = result['estimated_actuals'][0]['dni'] #Direct Normal Irradiance Center Value (W/m2)
dhi = result['estimated_actuals'][0]['dhi'] #Diffuse Horizontal Irradiance (W/m2)
cloud_opacity = result['estimated_actuals'][0]['cloud_opacity'] #Cloud Cover Factor/Opacity
period = result['estimated_actuals'][0]['period_end'] #Time Period Validity

#Print Results
print("Global Horizontal Irradiance Center Value (W/m2): " + str(ghi))
print("Direct (Beam) Horizontal Irradiance (W/m2): " + str(ebh))
print("Direct Normal Irradiance Center Value (W/m2): " + str(dni))
print("Diffuse Horizontal Irradiance (W/m2): " + str(dhi))
print("Cloud Cover Factor/Opacity: " + str(cloud_opacity))
print("Time Period Validity: " + str(period))

