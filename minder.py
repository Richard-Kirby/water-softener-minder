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

refill_warning = 500
all_ok_warning_time = 20 * 60 # time to wait if no warning.
warning_time = 5 * 60 # time to wait between warnings.


while True:
    dist_to_salt = time_of_flight.vl53.range

    if dist_to_salt < refill_warning:

        salt_str = "Distance to salt is {}.\n " \
                   "Re-fill needed at {}\n{}" .format(dist_to_salt, refill_warning,
                                                      datetime.datetime.now().strftime("%a %d/%m/%y %H:%M"))

        outgoing_telegram_queue.put_nowait(salt_str)
        time.sleep(all_ok_warning_time)

    else:

        salt_str = "WARNING: Distance to salt is {}.\n " \
                   "Re-fill needed at {}\n{}" .format(dist_to_salt, refill_warning,
                                                      datetime.datetime.now().strftime("%a %d/%m/%y %H:%M"))

        outgoing_telegram_queue.put_nowait(salt_str)

        time.sleep(warning_time)



