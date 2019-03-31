import random

import logging
import requests
import urllib
import json
import htmlmin
from typing import Any, Dict, Optional

from graphqlclient import GraphQLClient

client = GraphQLClient('https://arkive.herokuapp.com/v1alpha1/graphql')


XKCD_TEMPLATE_URL = 'https://xkcd.com/%s/info.0.json'
LATEST_XKCD_URL = 'https://xkcd.com/info.0.json'

class ARkiveHandler(object):
    '''
    This plugin provides several commands that can be used for fetch a comic
    strip from https://xkcd.com. The bot looks for messages starting with
    "@mention-bot" and responds with a message with the comic based on provided
    commands.
    '''

    META = {
        'name': 'ARkive',
        'description': 'Fetches comic strips from https://arkive.tech.',
    }

    def usage(self) -> str:
        print(self.findmeMajedaarID('happy'))

        return '''
                This plugin do something
            '''

    def findmeMajedaarID(self, k):

        result = client.execute('''
        query{
        ARs(where:{file: {_eq:"'''+k+'''"}}){
            file,
            name,
            NNJson,
            filePath,
            init,
            detectStateFn,
            created_by
        }
        }
        ''')
        res = json.loads(result)['data']['ARs']
        if len(res) == 0:
            return "oops nothing found"
        res = res[0]

        return res['created_by']
        # import urllib.request
        # data = str(urllib.request.urlopen('https://raw.githubusercontent.com/shashaBot/jeelizFaceFilter/master/index.html').read())
    
        # data = data.replace("{{filePath}}", res['filePath'])
        # data = data.replace("{{NNJson}}", res['NNJson'])
        # data = data.replace("{{detectStateFn}}", res['detectStateFn'])
        # data = data.replace("{{initSceneFn}}", res['init'])
        # data = data.replace("\n", "")
        # print(htmlmin.minify(data, remove_empty_space=True))
        # return urllib.parse.quote(htmlmin.minify(data, remove_empty_space=True))


    def findAndMake(self,c):
        # if c == "spaceship":
        # return "<a href='toApp://'>App</a>"
        return "[Checkout AR Experience]("+ self.findmeMajedaarID(c) +")"
        # return "[Checkout AR Experience](http://ARKive.tech/?q=" + self.findmeMajedaarID(c) +")"

    def searchAndMake(self, c, x):
        # if c == "search":

        result = client.execute('''
        query{
        ARs(where:{keywords: {_eq:"'''+x+'''"}}){
            file,
            name,
            NNJson,
            filePath,
            init,
            detectStateFn
        }
        }
        ''')
        res = json.loads(result)['data']['ARs']

        if len(res) == 0:
            return "oops nothing found"
        else:
            s = ""
            for r in res:
                s += r['name']+", "

            return "You can use:  "+ s[0:-1]

    def handle_message(self, message, bot_handler: Any) -> None:
        original_content = message['content']
        original_sender = message['sender_email']

        keywords = original_content.split(" ")
        print(keywords)
        if len(keywords) < 2:
            new_content = self.findAndMake(original_content)
        else:
            keys = keywords[1]
            new_content = self.searchAndMake(keywords[0], keys)
        # new_content = "you can use :D"

        bot_handler.send_reply(message, new_content)


class XkcdBotCommand(object):
    LATEST = 0
    RANDOM = 1
    COMIC_ID = 2

class XkcdNotFoundError(Exception):
    pass

class XkcdServerError(Exception):
    pass

def get_xkcd_bot_response(message: Dict[str, str], quoted_name: str) -> str:
    original_content = message['content'].strip()
    command = original_content.strip()

    commands_help = ("%s"
                     "\n* `{0} help` to show this help message."
                     "\n* `{0} latest` to fetch the latest comic strip from xkcd."
                     "\n* `{0} random` to fetch a random comic strip from xkcd."
                     "\n* `{0} <comic id>` to fetch a comic strip based on `<comic id>` "
                     "e.g `{0} 1234`.".format(quoted_name))

    try:
        if command == 'help':
            return commands_help % ('xkcd bot supports these commands:')
        elif command == 'latest':
            fetched = fetch_xkcd_query(XkcdBotCommand.LATEST)
        elif command == 'random':
            fetched = fetch_xkcd_query(XkcdBotCommand.RANDOM)
        elif command.isdigit():
            fetched = fetch_xkcd_query(XkcdBotCommand.COMIC_ID, command)
        else:
            return commands_help % ("xkcd bot only supports these commands, not `%s`:" % (command,))
    except (requests.exceptions.ConnectionError, XkcdServerError):
        logging.exception('Connection error occurred when trying to connect to xkcd server')
        return 'Sorry, I cannot process your request right now, please try again later!'
    except XkcdNotFoundError:
        logging.exception('XKCD server responded 404 when trying to fetch comic with id %s'
                          % (command))
        return 'Sorry, there is likely no xkcd comic strip with id: #%s' % (command,)
    else:
        return ("#%s: **%s**\n[%s](%s)" % (fetched['num'],
                                           fetched['title'],
                                           fetched['alt'],
                                           fetched['img']))

def fetch_xkcd_query(mode: int, comic_id: Optional[str]=None) -> Dict[str, str]:
    try:
        if mode == XkcdBotCommand.LATEST:  # Fetch the latest comic strip.
            url = LATEST_XKCD_URL

        elif mode == XkcdBotCommand.RANDOM:  # Fetch a random comic strip.
            latest = requests.get(LATEST_XKCD_URL)

            if latest.status_code != 200:
                raise XkcdServerError()

            latest_id = latest.json()['num']
            random_id = random.randint(1, latest_id)
            url = XKCD_TEMPLATE_URL % (str(random_id))

        elif mode == XkcdBotCommand.COMIC_ID:  # Fetch specific comic strip by id number.
            if comic_id is None:
                raise Exception('Missing comic_id argument')
            url = XKCD_TEMPLATE_URL % (comic_id)

        fetched = requests.get(url)

        if fetched.status_code == 404:
            raise XkcdNotFoundError()
        elif fetched.status_code != 200:
            raise XkcdServerError()

        xkcd_json = fetched.json()
    except requests.exceptions.ConnectionError as e:
        logging.exception("Connection Error")
        raise

    return xkcd_json

handler_class = ARkiveHandler
