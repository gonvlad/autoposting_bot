import json
import datetime
import time
import os
import requests
import telebot
from telebot import types
from boto.s3.connection import S3Connection


s3 = S3Connection(os.environ['S3_KEY'], os.environ['S3_SECRET'])
CHAT_ID = os.environ.get("CHAT_ID")
bot = telebot.TeleBot(s3)

def check_for_new_posts():
    '''Check instagram server for new posts
    '''

    # Logging date-time in comand prompt
    print("{0:=^37}".format("Request"))
    print("Date-Time: {0}".format(datetime.datetime.now()))

    # path to accounts.json
    path = "./accounts.json"

    # parse JSON
    with open(path, 'r') as json_data:
        profiles = list(json.load((json_data)))
        
        # work with every profile
        for profile in profiles:
            account_name = profile['account_name']
            account_id = profile['id']
            print("ID: {0} UserName: {1} => ".format(account_id, account_name), end="")

            # create the url
            url = 'https://www.instagram.com/{0}/?__a=1'.format(account_name)
            # get json-response
            response = requests.get(url).json()
    
            # check count of posts
            # number of posts from server
            posts_counter_server = response["graphql"]["user"]["edge_owner_to_timeline_media"]["count"]
            # number of posts from local db
            posts_counter_db = profile['posts']
            print(posts_counter_server, "posts")

            # Check for new posts
            if posts_counter_server != posts_counter_db:
                photo_url = grab_new_post(response)
                # send_new_post to telegram
                send_new_post(photo_url, account_name)
                # change posts counter in db
                profile["posts"] = posts_counter_server 

                # Null variables
                posts_counter_server = None
                posts_counter_db = None
                photo_url = None
            else:
                print("=> No new posts yet")

    with open(path, 'w') as json_data:
        json_data.write(json.dumps(profiles)) 
    # Just add empty line
    print()


def grab_new_post(response):
    '''Create url to latest post
    '''
    photo_url = response["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"][0]["node"]["display_url"]
    return photo_url


def send_new_post(photo_url, account_name):
    '''Send new to post to chat
    '''
    # Creates new keyboard and send to chat
    keyboard = create_keyboard(account_name)

    # send post to channel
    bot.send_photo(chat_id="-1001164551645", photo=photo_url, reply_markup=keyboard)
    print(f"=> New post by {account_name} sent")

def create_keyboard(account_name=None):
    keyboard = types.InlineKeyboardMarkup()
    buttons = types.InlineKeyboardButton(text="Перейти в Instagam", url=f'https://www.instagram.com/{account_name}/', callback_data="instagram")
    keyboard.add(buttons)
    return keyboard

if __name__ == "__main__":
    while True:
        try:
            check_for_new_posts()
            time.sleep(600)
        except KeyboardInterrupt:
            exit()
        except Exception as e:
            print(e)
            time.sleep(15)
