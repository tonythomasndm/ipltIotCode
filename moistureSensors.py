import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

class MoistureSensor:
    def __init__(self, i2c_bus=None, moistureThreshold=50):
        if i2c_bus is None:
            self.i2c = busio.I2C(board.SCL, board.SDA)
        else:
            self.i2c = i2c_bus

        self.ads = ADS.ADS1115(self.i2c)
        self.channels = [
            AnalogIn(self.ads, ADS.P0),
            AnalogIn(self.ads, ADS.P1),
            AnalogIn(self.ads, ADS.P2),
            AnalogIn(self.ads, ADS.P3)
        ]

        # Initial calibration values for max and min moisture levels
        self.limits = [
            {'max': 25100, 'min': 5500},
            {'max': 24900, 'min': 5500},
            {'max': 24980, 'min': 5500},
            {'max': 24480, 'min': 5500}
        ]
        self.moistureThreshold=moistureThreshold

    def readRawData(self):
        """Read raw data from all moisture sensors."""
        raw_data = {
            f'moisture_{i}': channel.value for i, channel in enumerate(self.channels)
        }
        return raw_data

    def readAveragedSensorValues(self, time_gap=1, num_readings=100):
        """Calculate averaged sensor values over a specified number of readings."""
        readings = [[] for _ in self.channels]
        for _ in range(num_readings):
            moisture_values = self.readRawData()
            for i, key in enumerate(moisture_values):
                readings[i].append(moisture_values[key])
            time.sleep(time_gap)

        averaged_values = [sum(channel_readings) / len(channel_readings) for channel_readings in readings]
        return averaged_values

    def calibrateSensors(self):
        """Calibrate sensors by setting the max and min limits based on current conditions."""
        print("Calibrating sensors, please ensure they are in the driest condition...")
        time.sleep(10)  # Small delay for the user to prepare the sensors
        print("Dry Calibration started")
        dry_values = self.readAveragedSensorValues()
        for i, avg in enumerate(dry_values):
            self.limits[i]['max'] = avg

        print("Dry calibration complete. Please ensure the sensors are now in the wettest condition...")
        time.sleep(20)  # Small delay for the user to prepare the sensors
        print("Wet Calibration started")
        wet_values = self.readAveragedSensorValues()
        for i, avg in enumerate(wet_values):
            self.limits[i]['min'] = avg

        print("Wet calibration complete. New limits are set.")

    def getMoisturePercentages(self):
        """Calculate moisture percentage for each sensor based on calibrated limits."""
        raw_data = self.readRawData()
        percentages = {}

        for i, key in enumerate(raw_data):
            value = raw_data[key]
            max_val = self.limits[i]['max']
            min_val = self.limits[i]['min']

            # Calculate percentage
            percentage = 100 * (max_val - value) / (max_val - min_val)
            percentage = max(0, min(100, percentage))  # Ensure the percentage is within 0-100

            percentages[key] = percentage

        return percentages

    def detectDrySoil(self, threshold=30):
        """Detect if the soil is dry based on a moisture threshold percentage."""
        moisture_percentages = self.getMoisturePercentages()
        dry_sensors = []

        for key, percentage in moisture_percentages.items():
            if percentage < threshold:
                dry_sensors.append(key)

        return dry_sensors

    def detectWetSoil(self, threshold=70):
        """Detect if the soil is wet based on a moisture threshold percentage."""
        moisture_percentages = self.getMoisturePercentages()
        wet_sensors = []

        for key, percentage in moisture_percentages.items():
            if percentage > threshold:
                wet_sensors.append(key)

        return wet_sensors

    def getSoilMoistureStatus(self):
        """Get a status message about the moisture condition of each sensor."""
        percentages = self.getMoisturePercentages()
        status = {}

        for key, percentage in percentages.items():
            if percentage < 30:
                status[key] = "Dry"
            elif 30 <= percentage <= 70:
                status[key] = "Moist"
            else:
                status[key] = "Wet"

        return status

    def printSensorReadings(self):
        """Prints raw and percentage readings for all sensors."""
        raw_data = self.readRawData()
        percentages = self.getMoisturePercentages()

        print("\nSensor Readings:")
        for key in raw_data:
            print(f"{key}: Raw Value = {raw_data[key]}, Moisture Percentage = {percentages[key]}%")

if __name__ == "__main__":
    sensor = MoistureSensor()

    # Calibrate the sensors (run once and save limits if needed)
    # sensor.calibrateSensors()

    while True:
        sensor.printSensorReadings()
        dry_sensors = sensor.detectDrySoil()
        wet_sensors = sensor.detectWetSoil()

        if dry_sensors:
            print(f"Dry soil detected on sensors: {dry_sensors}")

        if wet_sensors:
            print(f"Wet soil detected on sensors: {wet_sensors}")

        soil_status = sensor.getSoilMoistureStatus()
        print("Soil Moisture Status:", soil_status)

        time.sleep(5)
