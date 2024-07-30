from mpu6050 import mpu6050
import math
import time

class MPU6050:
    def __init__(self, address=0x68):
        self.sensor = mpu6050(address)
        self.accelOffset = {'x': 0, 'y': 0, 'z': 0}
        self.gyroOffset = {'x': 0, 'y': 0, 'z': 0}
        self.calibrateSensors()

    def getAcceleration(self):
        raw_accel = self.sensor.get_accel_data()
        return {
            'x': raw_accel['x'] - self.accelOffset['x'],
            'y': raw_accel['y'] - self.accelOffset['y'],
            'z': raw_accel['z'] - self.accelOffset['z']
        }

    def getGyroscope(self):
        raw_gyro = self.sensor.get_gyro_data()
        return {
            'x': raw_gyro['x'] - self.gyroOffset['x'],
            'y': raw_gyro['y'] - self.gyroOffset['y'],
            'z': raw_gyro['z'] - self.gyroOffset['z']
        }

    def getTemperature(self):
        """Get the temperature from the MPU6050."""
        return self.sensor.get_temp()

    def calibrateSensors(self):
        """Calibrate the accelerometer and gyroscope sensors."""
        accel_samples = {'x': 0, 'y': 0, 'z': 0}
        gyro_samples = {'x': 0, 'y': 0, 'z': 0}

        print("Calibrating sensors...")
        for _ in range(1000):
            accel_data = self.sensor.get_accel_data()
            gyro_data = self.sensor.get_gyro_data()

            accel_samples['x'] += accel_data['x']
            accel_samples['y'] += accel_data['y']
            accel_samples['z'] += accel_data['z']

            gyro_samples['x'] += gyro_data['x']
            gyro_samples['y'] += gyro_data['y']
            gyro_samples['z'] += gyro_data['z']

            time.sleep(0.01)

        self.accelOffset = {
            'x': accel_samples['x'] / 1000,
            'y': accel_samples['y'] / 1000,
            'z': accel_samples['z'] / 1000
        }

        self.gyroOffset = {
            'x': gyro_samples['x'] / 1000,
            'y': gyro_samples['y'] / 1000,
            'z': gyro_samples['z'] / 1000
        }
        print("Calibration complete.")

    def getOrientation(self):
        """Calculate pitch, roll, and yaw based on acceleration and gyroscope data."""
        accelData = self.getAcceleration()
        pitch = math.atan2(accelData['y'], accelData['z']) * 180 / math.pi
        roll = math.atan2(-accelData['x'], math.sqrt(accelData['y'] ** 2 + accelData['z'] ** 2)) * 180 / math.pi
        
        gyroData = self.getGyroscope()
        yaw = math.atan2(gyroData['y'], gyroData['x']) * 180 / math.pi

        return {'pitch': pitch, 'roll': roll, 'yaw': yaw}

    def detectMotion(self, threshold=0.5):
        """Detect significant motion based on acceleration magnitude."""
        accelData = self.getAcceleration()
        magnitude = math.sqrt(accelData['x']**2 + accelData['y']**2 + accelData['z']**2)
        return magnitude > threshold

    def getTiltInclination(self):
        """Calculate tilt angles along each axis."""
        accelData = self.getAcceleration()
        inclination = {
            'x': math.degrees(math.atan2(accelData['x'], math.sqrt(accelData['y'] ** 2 + accelData['z'] ** 2))),
            'y': math.degrees(math.atan2(accelData['y'], math.sqrt(accelData['x'] ** 2 + accelData['z'] ** 2))),
            'z': math.degrees(math.atan2(accelData['z'], math.sqrt(accelData['x'] ** 2 + accelData['y'] ** 2)))
        }
        return inclination

    def getSpeed(self, dt=1.0):
        """Calculate speed based on linear acceleration."""
        accelData = self.getAcceleration()
        speed = {
            'x': accelData['x'] * 9.81 * dt,
            'y': accelData['y'] * 9.81 * dt,
            'z': accelData['z'] * 9.81 * dt
        }
        return speed

    def getAngularAcceleration(self, dt=1.0):
        """Calculate angular acceleration based on gyroscope data."""
        angularVelocity = self.getGyroscope()
        angularAcceleration = {
            'x': angularVelocity['x'] * dt,
            'y': angularVelocity['y'] * dt,
            'z': angularVelocity['z'] * dt
        }
        return angularAcceleration

    def getAveragedValues(self, duration=10):
        """Calculate averaged acceleration and gyroscope values over a duration."""
        start_time = time.time()
        accel_samples = {'x': 0, 'y': 0, 'z': 0}
        gyro_samples = {'x': 0, 'y': 0, 'z': 0}
        count = 0

        while time.time() - start_time < duration:
            accel_data = self.getAcceleration()
            gyro_data = self.getGyroscope()

            accel_samples['x'] += accel_data['x']
            accel_samples['y'] += accel_data['y']
            accel_samples['z'] += accel_data['z']

            gyro_samples['x'] += gyro_data['x']
            gyro_samples['y'] += gyro_data['y']
            gyro_samples['z'] += gyro_data['z']

            count += 1
            time.sleep(0.01)  # Sample rate of 100 Hz

        averaged_accel = {
            'x': accel_samples['x'] / count,
            'y': accel_samples['y'] / count,
            'z': accel_samples['z'] / count
        }

        averaged_gyro = {
            'x': gyro_samples['x'] / count,
            'y': gyro_samples['y'] / count,
            'z': gyro_samples['z'] / count
        }

        return {'acceleration': averaged_accel, 'gyroscope': averaged_gyro}

    def detectShake(self, threshold=1.5):
        """Detect if the device is being shaken."""
        accelData = self.getAcceleration()
        magnitude = math.sqrt(accelData['x']**2 + accelData['y']**2 + accelData['z']**2)
        return magnitude > threshold

    def getMotionState(self):
        """Determine if the device is in motion or stationary."""
        accelData = self.getAcceleration()
        total_accel = math.sqrt(accelData['x']**2 + accelData['y']**2 + accelData['z']**2)
        
        # Threshold to differentiate between motion and stationary
        threshold = 0.2  # Adjust this value based on your application

        if total_accel > threshold:
            return "In Motion"
        else:
            return "Stationary"

if __name__ == "__main__":
    mpu = MPU6050()

    while True:
        print("\nInstantaneous Values:")
        print("Acceleration:", mpu.getAcceleration())
        print("Gyroscope:", mpu.getGyroscope())
        print("Temperature: {:.2f} C".format(mpu.getTemperature()))
        print("Orientation:", mpu.getOrientation())
        print("Tilt Inclination:", mpu.getTiltInclination())
        print("Speed:", mpu.getSpeed())
        print("Angular Acceleration:", mpu.getAngularAcceleration())
        print("Motion State:", mpu.getMotionState())

        if mpu.detectMotion(threshold=0.5):
            print("Motion Detected!")

        if mpu.detectShake(threshold=1.5):
            print("Shake Detected!")

        averaged_values = mpu.getAveragedValues(duration=10)
        print("\nAveraged Values over 10 seconds:")
        print("Acceleration:", averaged_values['acceleration'])
        print("Gyroscope:", averaged_values['gyroscope'])

        time.sleep(1)
