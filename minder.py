import time
import datetime
import threading
import queue
import sys
import ntplib
import json

import time_of_flight
import telegram_if
import led_strip
import graphing


# Standard time string
def std_time():
    return datetime.datetime.now().strftime("%a %d/%m/%y %H:%M")


# Main class for managing the Water Softener.
class WaterSoftenerMinder(threading.Thread):

    def __init__(self):
        super(WaterSoftenerMinder, self).__init__()

        print("Start up of Salt Minder - time might be off on reboot - no RTC", std_time())

        # Setting up the Telegram Interface
        # Set up the Telegram interface for outgoing messages.
        self.outgoing_telegram_queue = queue.Queue()
        self.incoming_telegram_queue = queue.Queue()

        self.telegram_interface = telegram_if.TelegramIf(self.outgoing_telegram_queue, self.incoming_telegram_queue)
        self.telegram_interface.daemon = True
        self.telegram_interface.start()

        # Set up the time of flight object.
        self.time_of_flight_thread = time_of_flight.TimeOfFlight()
        self.time_of_flight_thread.daemon = True
        self.time_of_flight_thread.start()

        # Set up the LED strip.
        # LED strip configuration:
        led_count = 22  # Number of LED pixels.
        led_pin = 18  # GPIO pin connected to the pixels (must support PWM!).
        led_freq_hz = 800000  # LED signal frequency in hertz (usually 800khz)
        led_dma = 5  # DMA channel to use for generating signal (try 5)
        led_brightness = 255  # Set to 0 for darkest and 255 for brightest
        led_invert = False  # True to invert the signal (when using NPN transistor level shift)

        # Queue for passing to the LED handler - this will display the level of salt in the hopper.
        self.led_remaining_salt_ratio_queue = queue.Queue()

        self.led_strip = led_strip.LedStripControl(led_count, led_pin, led_freq_hz, led_dma, led_invert, led_brightness,
                                                   self.led_remaining_salt_ratio_queue)
        self.led_strip.daemon = True
        self.led_strip.start()

        # Basic setup parameters - could go into a JSON or other file.
        self.hopper_size_mm = 420  # size of hopper in mm
        self.mm_to_salt_fill_line = 100  # distance between sensor and where the fill line is for the salt.
        self.refill_warning_ratio = 0.50  # Trigger a refill WARNING message at 20%
        self.refill_warning_level = self.refill_warning_ratio * (self.hopper_size_mm - self.mm_to_salt_fill_line)
        self.remaining_salt = 0
        self.remaining_salt_ratio = 0
        self.salt_str = None

        # hours at which to send a message to Telegram.  Don't send message while likely to be asleep.
        self.hours_to_message = [7, 20]
        self.hours_to_measure = [6]

        self.long_term_salt_data = []  # initialise the long term data with empty array - gets read from file.
        self.long_term_data_filename = 'long_term_salt_data.json'

        # Get the existing data from the file.
        try:
            with open(self.long_term_data_filename, 'r') as salt_data_file:
                self.long_term_salt_data = json.load(salt_data_file)
        except OSError:
            print("failure to read file {}".format(OSError.filename))

        # Create the plotter - plot up to 20 samples.
        self.salt_plotter = graphing.SaltPlotter(20)

        # check on the time sync.  If not synced yet, then wait and break out of the loop when detected or max loop
        # reached
        ntp_client = ntplib.NTPClient()

        # Give some maximum time to sync, otherwise crack on.
        for i in range(90):
            try:
                ntp_response = ntp_client.request('europe.pool.ntp.org', version=4)
                # print(ntp_response.offset)

                if ntp_response.offset < 2:
                    print("Synced @ {}" .format(i))
                    break

            except ntplib.NTPException:
                print("NTP Exception ")

            time.sleep(1)

    # Create the string to send for salt status.
    def create_salt_status_string(self):
        # Calculate how much salt is left.
        self.remaining_salt = self.hopper_size_mm - self.time_of_flight_thread.avg_measurement
        self.remaining_salt_ratio = float(self.remaining_salt / (self.hopper_size_mm - self.mm_to_salt_fill_line))

        # Check to prevent poor measurements - not sure if fails sometimes for some reason.
        if self.remaining_salt_ratio < 0:
            self.remaining_salt_ratio = 0
        elif self.remaining_salt_ratio > 1:  # might be overfilled a bit higher than the maximum fill line.
            self.remaining_salt_ratio = 1

        # Create a status string, which may not get sent anywhere.
        self.salt_str = "Remaining salt is {:.0%} or {:.0f}mm.\n" \
                        "Re-fill needed at {:.0%} or {:.0f}mm\n{}.".format(self.remaining_salt_ratio,
                                                                           self.remaining_salt,
                                                                           self.refill_warning_ratio,
                                                                           self.refill_warning_level,
                                                                           std_time())

        # Change the message to prepend Warning if salt is low.
        if self.remaining_salt_ratio < self.refill_warning_ratio:
            self.salt_str = "WARNING LOW SALT" + self.salt_str

        return self.salt_str

    # This responds to incoming requests to the bot.
    def respond_to_command(self):

        while not self.incoming_telegram_queue.empty():
            command = self.incoming_telegram_queue.get_nowait()
            print("Processing command = ", command)

            if command == '/salt':
                if self.salt_str is not None:
                    self.outgoing_telegram_queue.put_nowait(
                        telegram_if.OutgoingTelegramItem(string_to_send=self.salt_str))

                else:
                    self.outgoing_telegram_queue.put_nowait(
                        telegram_if.OutgoingTelegramItem(string_to_send="No Salt String - try later"))

            elif command == '/time':

                self.outgoing_telegram_queue.put_nowait(
                    telegram_if.OutgoingTelegramItem(string_to_send=std_time()))

            elif command == '/history':
                out_telegram_item = telegram_if.OutgoingTelegramItem\
                    (image_to_send_dict={'image': "/home/pi/water-softener-minder/salt_plot.jpg",
                                         'caption': self.salt_str})

                self.outgoing_telegram_queue.put_nowait(out_telegram_item)

            else:
                out_telegram_item = telegram_if.OutgoingTelegramItem (string_to_send=
                                                                      "I didn't understand " + command +
                                                                      "\nTry /salt or /history or /time")

                self.outgoing_telegram_queue.put_nowait(out_telegram_item)

    def regular_measurement(self, curr_time):
        print("WSM: {}" .format(self.salt_str))
        data_item = {"datetime": curr_time.strftime("%d/%m %H:%M"), "salt_level": self.remaining_salt}
        self.long_term_salt_data.append(data_item)

        # Update the plot and write latest data to the file.
        if len(self.long_term_salt_data) >= 5:
            self.salt_plotter.plot_save(self.long_term_salt_data, "salt_plot.jpg")

            # Write the latest data to file.  Only save last 200 results
            with open(self.long_term_data_filename, 'w') as salt_data_file:
                json.dump(self.long_term_salt_data[-200:], salt_data_file)

    # Main loop that manages the work flow.
    def run(self):
        last_msg_day_hour = None  # initialising this so we get one status message sent at the start.
        last_measure_day_hour = None  # Init of the measurement day/hour
        time.sleep(5)  # wait a few seconds to build up some measurements.

        # Main loop.
        while True:
            curr_time = datetime.datetime.now()
            curr_day_hour = {'day': curr_time.day, 'hour':curr_time.hour}

            # Get the salt string, which provides the status of the hopper.
            self.create_salt_status_string()

            # Check to see if there is any commend to respond to - check incoming
            self.respond_to_command()

            # This goes to LED string for handling.
            self.led_remaining_salt_ratio_queue.put_nowait(self.remaining_salt_ratio)

            # Restricts the time at which measurements are taken.  The last_measurement_hour bit makes sure
            # only one measurement gets done in that one hour.
            if curr_time.hour in self.hours_to_measure and not curr_day_hour == last_measure_day_hour:
                # Take the regular measurement
                #print(curr_day_hour, last_measure_day_hour)
                self.regular_measurement(curr_time)
                last_measure_day_hour = curr_day_hour

            # Restricts the time at which measurements are announced to telegram.  The last_msg_hour bit makes sure
            # only one message goes out in that one hour.
            if (curr_time.hour in self.hours_to_message and not curr_day_hour == last_msg_day_hour) \
                    or last_msg_day_hour is None:

                # Send the latest image
                image_dict = {'image': "/home/pi/water-softener-minder/salt_plot.jpg", 'caption': self.salt_str}
                out_telegram_item = telegram_if.OutgoingTelegramItem(image_to_send_dict=image_dict)
                self.outgoing_telegram_queue.put_nowait(out_telegram_item)
                last_msg_day_hour = curr_day_hour

            time.sleep(10)


# Starting up the main object that manages everything.
water_softener_minder = WaterSoftenerMinder()
water_softener_minder.isDaemon = True
water_softener_minder.start()

try:
    while True:

        # All the work is being done in separate threads.
        time.sleep(60)

except KeyboardInterrupt:
    print("Exiting due to KB interrupt")

finally:
    print("*** Water-Softener-Minder is dead")
    sys.exit(0)

