import json
import threading
import time
import datetime
import sys
import os

import telepot
from telepot.loop import MessageLoop

telegram_bot_global = None


# Class that manages the TFL status - sorts out the credentials and makes the queries when asked.
class TelegramIf(threading.Thread):
    #global telegram_bot_global

    # Get setup, including reading in credentials from the JSON file.  Credentials need to be obtained from TFL.
    def __init__(self, out_queue, in_queue):
        # Init the threading
        super(TelegramIf, self).__init__()

        # Grab the credentials.  TODO: everyone has to get their own credentials.  Not in the repo.
        with open('telegram_if/telegram_bot_token.secret') as json_data_file:
            config = json.load(json_data_file)

        # assign to appropriate variables - get used for each call to get status.
        self.telegram_bot = telepot.Bot(config['telegram_secret']['http_api_token'])
        self.telegram_user_id = config['telegram_secret']['telegram_user_id']

        self.bot_dict = self.telegram_bot.getMe()

        # print(self.bot_dict)

        # Set last update to 0 - this means will process all new messages.
        self.last_update_id = 0

        self.outgoing_queue = out_queue
        self.incoming_queue = in_queue

    # Run function is to be over-ridden as it is the main function that is used by the Thread class.
    def run(self):

        print("Telegram IF up and listening")

        try:
            self.telegram_bot.sendMessage(self.telegram_user_id, "water-softener-minder bot restart\n{}"
                                         .format(datetime.datetime.now().strftime("%a %d/%m/%y %H:%M")))

            #self.telegram_bot.sendMessage(0, "water-softener-minder bot restart\n{}"
            #                              .format(datetime.datetime.now().strftime("%a %d/%m/%y %H:%M")))
            # Get the status every once in a while
            str_to_send = None

            while True:

                # print("Running")

                # Get any messages that have to be dealt with.  Offset is the next message to deal with.
                try:
                    response = self.telegram_bot.getUpdates(offset=self.last_update_id + 1)
                except:
                    print("*** ERR- failed to check for messages - not panicking")

                for update in response:
                    self.last_update_id = update['update_id']
                    # print(update)

                    command = update['message']['text']
                    # chat_id = update['message']['chat']['id']

                    # print('Got command: {}'.format(command))

                    # Put into the queue for the minder main program to handle.
                    self.incoming_queue.put_nowait(command)

                while not self.outgoing_queue.empty():
                    str_to_send = self.outgoing_queue.get_nowait()

                # Send any string that needs to be sent.
                if str_to_send is not None:
                    self.telegram_bot.sendMessage(self.telegram_user_id, str_to_send)
                    str_to_send = None

                time.sleep(30)

        except KeyboardInterrupt:

            print("Keyboard Interrupt")

        except:
            print("***** Water-Softener-Minder - Some other exception - might be a network issue - 120s stale task timeout?")

            print("***** Water-Softener-Minder - Unexpected error:", sys.exc_info())
            # Force Reboot here after a timeout.
            print("***** Water-Softener-Minder - Forcing Reboot in 300s")

            time.sleep(300)  # wait a few seconds to give a chance to break a vicious cycle if needed Ctrl C will stop.

            print("***** Water-Softener-Minder - issuing *****sudo reboot --force*****")
            os.system('/usr/bin/sudo reboot --force')

        finally:
            print("Ending of Telegram Interface Thread")



"""
After **inserting token** in the source code, run it:
```
$ python2.7 diceyclock.py
```
[Here is a tutorial](http://www.instructables.com/id/Set-up-Telegram-Bot-on-Raspberry-Pi/)
teaching you how to setup a bot on Raspberry Pi. This simple bot does nothing
but accepts two commands:
- `/roll` - reply with a random integer between 1 and 6, like rolling a dice.
- `/time` - reply with the current time, like a clock.
"""

if __name__ == "__main__":
    telegram_if = TelegramIf()
    # tfl_status.get_summary_status()
    telegram_if.start()

    MessageLoop(telegram_if.telegram_bot, handle).run_as_thread()

    print('I am listening ...')

    telegram_if.telegram_bot.sendMessage(telegram_if.telegram_user_id, "Water Softener Minder Bot restart")

    while 1:
        time.sleep(10)
