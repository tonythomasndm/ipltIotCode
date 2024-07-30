import time
import os
import pigpio
import requests

class GpsModule:
    def __init__(self, txPin, rxPin, baudRate=9600, byteBits=8, mappls_api_key=None):
        self.txPin = txPin
        self.rxPin = rxPin
        self.baudRate = baudRate
        self.byteBits = byteBits
        self.mappls_api_key = mappls_api_key

        self.pi = pigpio.pi()
        if not self.pi.connected:
            os.system('sudo pigpiod')
            time.sleep(1)
            self.pi = pigpio.pi()
        if not self.pi.connected:
            raise Exception("Can't connect to pigpio daemon")

        self.pi.set_mode(self.txPin, pigpio.OUTPUT)
        self.pi.set_mode(self.rxPin, pigpio.INPUT)
        self.pi.bb_serial_read_open(self.rxPin, self.baudRate, self.byteBits)

        self.resetGpsData()

    def resetGpsData(self):
        self.latitude = None
        self.longitude = None
        self.latitudeDirection = None
        self.longitudeDirection = None
        self.speed = None
        self.altitude = None
        self.fixQuality = None
        self.numSatellites = None
        self.hdop = None
        self.time = None
        self.date = None

    def parseGprmcSentence(self, sentence):
        parts = sentence.split(',')
        if len(parts) > 2 and parts[2] == 'A':  # Data status A=Active, V=Void
            self.time = parts[1]
            self.latitude, self.latitudeDirection = self.convertToDecimal(parts[3], parts[4])
            self.longitude, self.longitudeDirection = self.convertToDecimal(parts[5], parts[6])
            self.speed = float(parts[7]) * 1.852 if parts[7] else None  # Convert knots to km/h if speed is available
            self.date = parts[9]

    def parseGpggaSentence(self, sentence):
        parts = sentence.split(',')
        if len(parts) < 15:
            return False
        try:
            self.latitude = float(parts[2])
            self.latitudeDirection = parts[3]
            self.longitude = float(parts[4])
            self.longitudeDirection = parts[5]
            self.fixQuality = int(parts[6])
            self.numSatellites = int(parts[7])
            self.hdop = float(parts[8])
            self.altitude = float(parts[9])
            self.time = parts[1]

            # Convert latitude and longitude to decimal degrees
            self.latitude = self.convertToDecimalDegree(self.latitude, self.latitudeDirection)
            self.longitude = self.convertToDecimalDegree(self.longitude, self.longitudeDirection)

            return True
        except ValueError:
            return False

    def parseGpvtgSentence(self, sentence):
        parts = sentence.split(',')
        self.speed = float(parts[7]) if parts[7] else None  # Speed over ground in km/h if speed is available

    def convertToDecimal(self, degreeMin, direction):
        if not degreeMin or not direction:
            return None, None
        degree = float(degreeMin[:2])
        minute = float(degreeMin[2:])
        decimal = degree + (minute / 60)
        if direction in ['S', 'W']:
            decimal = -decimal
        return decimal, direction

    def convertToDecimalDegree(self, value, direction):
        degree = int(value / 100)
        minute = value % 100
        decimal = degree + (minute / 60)
        if direction in ['S', 'W']:
            decimal = -decimal
        return decimal

    def readData(self):
        (count, data) = self.pi.bb_serial_read(self.rxPin)
        if count:
            gpsData = data.decode('utf-8', 'ignore')
            for line in gpsData.split('\r\n'):
                if line.startswith('$GPRMC'):
                    if len(line.split(',')) >= 10:  # Ensure there are enough parts
                        self.parseGprmcSentence(line)
                elif line.startswith('$GPGGA'):
                    if len(line.split(',')) >= 15:  # Ensure there are enough parts
                        self.parseGpggaSentence(line)
                elif line.startswith('$GPVTG'):
                    if len(line.split(',')) >= 8:  # Ensure there are enough parts
                        self.parseGpvtgSentence(line)

    def getGpsDetails(self):
        self.readData()
        return {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'latitudeDirection': self.latitudeDirection,
            'longitudeDirection': self.longitudeDirection,
            'speed': self.speed,
            'altitude': self.altitude,
            'fixQuality': self.fixQuality,
            'numSatellites': self.numSatellites,
            'hdop': self.hdop,
            'time': self.time,
            'date': self.date
        }

    def close(self):
        self.pi.bb_serial_read_close(self.rxPin)
        self.pi.stop()

    def getLocationName(self, latitude, longitude):
        if self.mappls_api_key is None:
            return 'Unknown location'
        
        url = f'https://apis.mapmyindia.com/advancedmaps/v1/{self.mappls_api_key}/rev_geocode?lat={latitude}&lng={longitude}'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            address = data.get('results', [{}])[0].get('formatted_address', 'Unknown location')
            return address
        else:
            return 'Unknown location'

if __name__ == "__main__":
    mappls_api_key = '0fbd2bdf56e454036ea46fcee4559d05'
    gps = GpsModule(txPin=5, rxPin=6, mappls_api_key=mappls_api_key)  # Updated to use GPIO 5 and GPIO 6

    print("Reading GPS data...")
    try:
        time.sleep(2)  # Allow some time for GPS module to initialize and get a fix
        while True:
            gpsDetails = gps.getGpsDetails()
            if gpsDetails['latitude'] is not None and gpsDetails['longitude'] is not None:
                location_name = gps.getLocationName(gpsDetails['latitude'], gpsDetails['longitude'])
                print(f"Latitude: {gpsDetails['latitude']}° {gpsDetails['latitudeDirection']}, Longitude: {gpsDetails['longitude']}° {gpsDetails['longitudeDirection']}")
                print(f"Nearest Place: {location_name}")
                print(f"Speed: {gpsDetails['speed']} km/h")
                print(f"Altitude: {gpsDetails['altitude']} m")
                print(f"Fix Quality: {gpsDetails['fixQuality']}")
                print(f"Number of Satellites: {gpsDetails['numSatellites']}")
                print(f"HDOP: {gpsDetails['hdop']}")
                print(f"Time: {gpsDetails['time']}")
                print(f"Date: {gpsDetails['date']}")
            else:
                print("No valid data received. Retrying...")
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        gps.close()
import time
import os
import pigpio
import requests

class GpsModule:
    def __init__(self, txPin, rxPin, baudRate=9600, byteBits=8, mappls_api_key=None):
        self.txPin = txPin
        self.rxPin = rxPin
        self.baudRate = baudRate
        self.byteBits = byteBits
        self.mappls_api_key = mappls_api_key

        self.pi = pigpio.pi()
        if not self.pi.connected:
            os.system('sudo pigpiod')
            time.sleep(1)
            self.pi = pigpio.pi()
        if not self.pi.connected:
            raise Exception("Can't connect to pigpio daemon")

        self.pi.set_mode(self.txPin, pigpio.OUTPUT)
        self.pi.set_mode(self.rxPin, pigpio.INPUT)
        self.pi.bb_serial_read_open(self.rxPin, self.baudRate, self.byteBits)

        self.resetGpsData()

    def resetGpsData(self):
        self.latitude = None
        self.longitude = None
        self.latitudeDirection = None
        self.longitudeDirection = None
        self.speed = None
        self.altitude = None
        self.fixQuality = None
        self.numSatellites = None
        self.hdop = None
        self.time = None
        self.date = None

    def parseGprmcSentence(self, sentence):
        parts = sentence.split(',')
        if len(parts) > 2 and parts[2] == 'A':  # Data status A=Active, V=Void
            self.time = parts[1]
            self.latitude, self.latitudeDirection = self.convertToDecimal(parts[3], parts[4])
            self.longitude, self.longitudeDirection = self.convertToDecimal(parts[5], parts[6])
            self.speed = float(parts[7]) * 1.852 if parts[7] else None  # Convert knots to km/h if speed is available
            self.date = parts[9]

    def parseGpggaSentence(self, sentence):
        parts = sentence.split(',')
        if len(parts) < 15:
            return False
        try:
            self.latitude = float(parts[2])
            self.latitudeDirection = parts[3]
            self.longitude = float(parts[4])
            self.longitudeDirection = parts[5]
            self.fixQuality = int(parts[6])
            self.numSatellites = int(parts[7])
            self.hdop = float(parts[8])
            self.altitude = float(parts[9])
            self.time = parts[1]

            # Convert latitude and longitude to decimal degrees
            self.latitude = self.convertToDecimalDegree(self.latitude, self.latitudeDirection)
            self.longitude = self.convertToDecimalDegree(self.longitude, self.longitudeDirection)

            return True
        except ValueError:
            return False

    def parseGpvtgSentence(self, sentence):
        parts = sentence.split(',')
        self.speed = float(parts[7]) if parts[7] else None  # Speed over ground in km/h if speed is available

    def convertToDecimal(self, degreeMin, direction):
        if not degreeMin or not direction:
            return None, None
        degree = float(degreeMin[:2])
        minute = float(degreeMin[2:])
        decimal = degree + (minute / 60)
        if direction in ['S', 'W']:
            decimal = -decimal
        return decimal, direction

    def convertToDecimalDegree(self, value, direction):
        degree = int(value / 100)
        minute = value % 100
        decimal = degree + (minute / 60)
        if direction in ['S', 'W']:
            decimal = -decimal
        return decimal

    def readData(self):
        (count, data) = self.pi.bb_serial_read(self.rxPin)
        if count:
            gpsData = data.decode('utf-8', 'ignore')
            for line in gpsData.split('\r\n'):
                if line.startswith('$GPRMC'):
                    if len(line.split(',')) >= 10:  # Ensure there are enough parts
                        self.parseGprmcSentence(line)
                elif line.startswith('$GPGGA'):
                    if len(line.split(',')) >= 15:  # Ensure there are enough parts
                        self.parseGpggaSentence(line)
                elif line.startswith('$GPVTG'):
                    if len(line.split(',')) >= 8:  # Ensure there are enough parts
                        self.parseGpvtgSentence(line)

    def getGpsDetails(self):
        self.readData()
        return {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'latitudeDirection': self.latitudeDirection,
            'longitudeDirection': self.longitudeDirection,
            'speed': self.speed,
            'altitude': self.altitude,
            'fixQuality': self.fixQuality,
            'numSatellites': self.numSatellites,
            'hdop': self.hdop,
            'time': self.time,
            'date': self.date
        }

    def close(self):
        self.pi.bb_serial_read_close(self.rxPin)
        self.pi.stop()

    def getLocationName(self, latitude, longitude):
        if self.mappls_api_key is None:
            return 'Unknown location'
        
        url = f'https://apis.mapmyindia.com/advancedmaps/v1/{self.mappls_api_key}/rev_geocode?lat={latitude}&lng={longitude}'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            address = data.get('results', [{}])[0].get('formatted_address', 'Unknown location')
            return address
        else:
            return 'Unknown location'

if __name__ == "__main__":
    mappls_api_key = '0fbd2bdf56e454036ea46fcee4559d05'
    gps = GpsModule(txPin=5, rxPin=6, mappls_api_key=mappls_api_key)  # Updated to use GPIO 5 and GPIO 6

    print("Reading GPS data...")
    try:
        time.sleep(2)  # Allow some time for GPS module to initialize and get a fix
        while True:
            gpsDetails = gps.getGpsDetails()
            if gpsDetails['latitude'] is not None and gpsDetails['longitude'] is not None:
                location_name = gps.getLocationName(gpsDetails['latitude'], gpsDetails['longitude'])
                print(f"Latitude: {gpsDetails['latitude']}° {gpsDetails['latitudeDirection']}, Longitude: {gpsDetails['longitude']}° {gpsDetails['longitudeDirection']}")
                print(f"Nearest Place: {location_name}")
                print(f"Speed: {gpsDetails['speed']} km/h")
                print(f"Altitude: {gpsDetails['altitude']} m")
                print(f"Fix Quality: {gpsDetails['fixQuality']}")
                print(f"Number of Satellites: {gpsDetails['numSatellites']}")
                print(f"HDOP: {gpsDetails['hdop']}")
                print(f"Time: {gpsDetails['time']}")
                print(f"Date: {gpsDetails['date']}")
            else:
                print("No valid data received. Retrying...")
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        gps.close()
