# Simple demo of the VL53L0X distance sensor.
# Will print the sensed range/distance every second.
import time
import threading

import board
import busio

import adafruit_vl53l0x


# Class to manage the Time of Flight Sensor.
class TimeOfFlight(threading.Thread):

    def __init__(self):
        super(TimeOfFlight, self).__init__()

        # Initialize I2C bus and sensor.
        i2c = busio.I2C(board.SCL, board.SDA)
        self.vl53 = adafruit_vl53l0x.VL53L0X(i2c)

        self.vl53.measurement_timing_budget = 200000

        self.past_measures = []
        self.avg_measurement = 0

        # Optionally adjust the measurement timing budget to change speed and accuracy.
        # See the example here for more details:
        #   https://github.com/pololu/vl53l0x-arduino/blob/master/examples/Single/Single.ino
        # For example a higher speed but less accurate timing budget of 20ms:
        #vl53.measurement_timing_budget = 20000
        # Or a slower but more accurate timing budget of 200ms:
        #vl53.measurement_timing_budget = 200000
        # The default timing budget is 33ms, a good compromise of speed and accuracy.

    # This runs when the thread is started.
    def run(self):
        time.sleep(2)

        while True:
            #print('Range: {0}mm'.format(self.vl53.range))
            if len(self.past_measures) == 20:
                self.past_measures.pop(0)

            self.past_measures.append(self.vl53.range)
            self.avg_measurement = sum(self.past_measures)/len(self.past_measures)
            time.sleep(5)
            #print("Average {} sum {} count {}".format( self.avg_measurement, sum(self.past_measures), len(self.past_measures)))



# Main loop will read the range and print it every second.

if __name__ == "__main__":
    while True:
        print('Range: {0}mm'.format(vl53.range))
        time.sleep(1.0)
