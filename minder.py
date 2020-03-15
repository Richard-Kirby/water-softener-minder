import time
import datetime
import queue

import time_of_flight
import telegram_if
import led_strip
from telepot.loop import MessageLoop


# Standard time string
def std_time():
    return datetime.datetime.now().strftime("%a %d/%m/%y %H:%M")


# This handles incoming telegram comms.
def incoming_telegram_handle(msg):
    chat_id = msg['chat']['id']
    command = msg['text']

    print(chat_id)

    print('Got command: {}'.format(command))

    # Handles the various commands coming in.
    if command == '/salt':
        telegram_interface.telegram_bot.sendMessage(chat_id, "Salt Level: {} {}".format(time_of_flight.vl53.range, std_time()))
    elif command == '/time':
        telegram_interface.telegram_bot.sendMessage(chat_id, std_time())
    else:
        telegram_interface.telegram_bot.sendMessage(chat_id, "I didn't understand "+ command + "\nTry /salt or /time")


# Set up the Telegram interface for outgoing messages.
outgoing_telegram_queue = queue.Queue()

telegram_interface = telegram_if.TelegramIf(outgoing_telegram_queue)
telegram_interface.daemon = True
telegram_interface.start()

MessageLoop(telegram_interface.telegram_bot, incoming_telegram_handle).run_as_thread()

# Set up the time of flight object.
time_of_flight = time_of_flight.TimeOfFlight()
time_of_flight.daemon = True
time_of_flight.start()

# Set up the LED strip.
# LED strip configuration:
LED_COUNT = 22  # Number of LED pixels.
LED_PIN = 18  # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 5  # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)

# Queue for passing to the LED handler - this will display the level of salt in the hopper.
led_remaining_salt_ratio_queue = queue.Queue()

led_strip = led_strip.LedStripControl(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS,
                                      led_remaining_salt_ratio_queue)
led_strip.daemon = True
led_strip.start()

# Basic setup parameters - could go into a JSON or other file.
hopper_size_mm = 420 # size of hopper in mm
mm_to_salt_fill_line = 100 # distance between sensor and where the fill line is for the salt.
refill_warning_ratio = 0.20 # Trigger a refill WARNING message at 20%
all_ok_time = 4 * 60 * 60 # time to wait if no warning.
warning_time = 60 * 60 # time to wait between warnings.

# hours at which to send a message to Telegram.  Don't send message while likely to be asleep.
hours_to_message = [7, 18, 20]
time.sleep(90)  # giving a bit of time in case the Pi just started.  Poor little thing doesn't keep track of time.
last_msg_hour = None  # last message sent - if None, it indicates the program is just starting.

# Main loop.
while True:

    print("Measuring")
    # Calculate how much salt is left.
    remaining_salt = hopper_size_mm - time_of_flight.vl53.range
    remaining_salt_ratio = float(remaining_salt / (hopper_size_mm - mm_to_salt_fill_line))

    # Check to prevent poor measurements - not sure if fails sometimes for some reason.
    if remaining_salt_ratio < 0:
        remaining_salt_ratio = 0
    elif remaining_salt_ratio > 1:  # might be overfilled a bit higher than the maximum fill line.
        remaining_salt_ratio = 1

    curr_time = datetime.datetime.now()

    # Create a status string, which may not get sent anywhere.
    salt_str = "Remaining salt is {:.0%} or {}mm .\n" \
               "Re-fill needed at {:.0%} or {}mm\n{}".format(remaining_salt_ratio,
                                                             remaining_salt,
                                                             refill_warning_ratio,
                                                             refill_warning_ratio * (hopper_size_mm
                                                                                     - mm_to_salt_fill_line),
                                                             std_time())

    # Change the message to prepend Warning if salt is low.
    if remaining_salt_ratio < refill_warning_ratio:
        salt_str = "WARNING LOW SALT" + salt_str

    print(salt_str)

    # This goes to LED string for handling.
    led_remaining_salt_ratio_queue.put_nowait(remaining_salt_ratio)

    # Restricts the time at which measurements are announced to telegram.  The last_msg_hour bit makes sure
    # only one message goes out in that one hour.
    if (curr_time.hour in hours_to_message and curr_time.hour is not last_msg_hour) or last_msg_hour is None:

        outgoing_telegram_queue.put_nowait(salt_str)
        last_msg_hour = curr_time.hour

    time.sleep(30)