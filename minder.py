import time
import datetime
import queue

import time_of_flight
import telegram_if

outgoing_telegram_queue = queue.Queue()

telegram_interface = telegram_if.TelegramIf(outgoing_telegram_queue)
telegram_if.daemon = True
telegram_interface.start()

time_of_flight = time_of_flight.TimeOfFlight()
time_of_flight.daemon = True
time_of_flight.start()

refill_warning = 300
all_ok_time = 4 * 60 * 60 # time to wait if no warning.
warning_time = 60 * 60 # time to wait between warnings.

first_message_hour = 7  # first message of the day
last_message_hour = 20  # last message of the day

time.sleep(90)  # giving a bit of time in case the Pi just started.  Poor little thing doesn't keep track of time.

while True:
    dist_to_salt = time_of_flight.vl53.range

    # Check to prevent poor measurements - not sure if fails sometimes for some reason. 
    if dist_to_salt > 8000:
        dist_to_salt = 0

    curr_time = datetime.datetime.now()
    print(curr_time.hour)

    # Restricts the time at which measurements are announced.
    if int(first_message_hour) <= int(curr_time.hour) <= int(last_message_hour):

        print("Checking")

        if dist_to_salt < refill_warning:

            print("Salt is OK")

            salt_str = "Distance to salt is {}.\n" \
                       "Re-fill needed at {}\n{}" .format(dist_to_salt, refill_warning,
                                                          datetime.datetime.now().strftime("%a %d/%m/%y %H:%M"))

            outgoing_telegram_queue.put_nowait(salt_str)
            time.sleep(all_ok_time)

        else:

            print("LOW Salt")

            salt_str = "WARNING: Distance to salt is {}.\n" \
                       "Re-fill needed at {}\n{}" .format(dist_to_salt, refill_warning,
                                                          datetime.datetime.now().strftime("%a %d/%m/%y %H:%M"))

            outgoing_telegram_queue.put_nowait(salt_str)

            time.sleep(warning_time)

    time.sleep(30)

