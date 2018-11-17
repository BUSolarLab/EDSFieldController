# https://docs.python.org/2/library/csv.html

import csv

class csvFile:
    def writeIsc(fileName, time, Isc_1, Isc_2, Isc_3, Isc_4, Isc_5, Isc_6, Isc_7, Isc_8):
        with open(fileName, 'wb') as csvfile:
            iscwriter = csv.writer(csvfile, delimiter=',')
            iscwriter.writerow(time, Isc_1, Isc_2, Isc_3, Isc_4, Isc_5, Isc_6, Isc_7, Isc_8)

    def writeWeatherData(fileName, time, temp, humidity):
        with open(fileName, 'wb') as csvfile:
            weatherwriter = csv.writer(csvfile, delimiter=',')
            weatherwriter.writerow(time, temp, humidity)

