import json
import threading
import time
import datetime

import telepot
from telepot.loop import MessageLoop


# Class that manages the TFL status - sorts out the credentials and makes the queries when asked.
class TelegramIf(threading.Thread):

    # Get setup, including reading in credentials from the JSON file.  Credentials need to be obtained from TFL.
    def __init__(self):
        # Init the threading
        super(TelegramIf, self).__init__()

        # Grab the credentials.  TODO: everyone has to get their own credentials.  Not in the repo.
        with open('telegram-if/telegram-bot-token.secret') as json_data_file:
            config = json.load(json_data_file)

        # assign to appropriate variables - get used for each call to get status.
        self.telegram_bot = telepot.Bot(config['telegram_secret']['http_api_token'])
        self.telegram_user_id = config['telegram_secret']['telegram_user_id']

        self.bot_dict = self.telegram_bot.getMe()

        print(self.bot_dict)


    # Get the status from the TFL site and process it to get just the summary status.
    '''
    def get_summary_status(self):

        status ={}

        try:
            print("trying")
            result= requests.get(self.status_request_url).json()
            for line in result:
                print (line['name'],":", line['lineStatuses'][0]['statusSeverityDescription'])
                status[line['name']] = line['lineStatuses'][0]['statusSeverityDescription']
        except:
            print("tfl status get failed - random number generator or Internet not avail?")
            raise

        #print(status)
        return status
    '''

    def run(self):
        # trying to ensure there is enough entropy to get started.  Just wait for 5 min.  Could be more clever.
        #time.sleep(300)

        # Get the status every once in a while
        while True:
            print("Running")
            time.sleep(120)

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

def handle(msg):
    chat_id = msg['chat']['id']
    command = msg['text']

    print(chat_id)

    print('Got command: {}'.format(command))

    if command == '/salt':
        telegram_if.telegram_bot.sendMessage(chat_id, "salt")
    elif command == '/time':
        telegram_if.telegram_bot.sendMessage(chat_id, str(datetime.datetime.now()))
    else:
        telegram_if.telegram_bot.sendMessage(chat_id, "I didn't understand "+ command + "\nTry /salt or /time")


if __name__ == "__main__":
    telegram_if = TelegramIf()
    #tfl_status.get_summary_status()
    telegram_if.start()

    MessageLoop(telegram_if.telegram_bot, handle).run_as_thread()

    print('I am listening ...')

    telegram_if.telegram_bot.sendMessage(telegram_if.telegram_user_id, "Water Softener Bot restart")

    while 1:
        time.sleep(10)
