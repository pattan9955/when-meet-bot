import json
import requests
import time
import telegram
import pyrebase

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters, updater

from secret_token import * #local secret.py file

URL = "https://api.telegram.org/bot{}/".format(TOKEN)

# Connect to Firebase db
config = {
    "apiKey": "AIzaSyAIioaoGBYY8Hl0fguaCRWWL7wpCPb0wSo",
    "authDomain": "whenmeetbot.firebaseapp.com",
    "databaseURL": "https://whenmeetbot-default-rtdb.asia-southeast1.firebasedatabase.app",
    "storageBucket": "whenmeetbot.appspot.com"
  }
firebase = pyrebase.initialize_app(config)

#TODO
def start(update, context):
    username = update.message.from_user.username
    welcome = '''Welcome to WhenMeetBot!\nFor help, type '/help'.\nTo upload your .ics file, type '/upload'.\nTo query for common free times, type '/find'.'''
    
#TODO
def help(update, context):
    pass

#TODO
def find(update, context):
    pass

#TODO
def upload(update, context):
    pass

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher;

    # Add command handler for initializing bot
    dp.add_handler(CommandHandler('start', start))

    # Add commmand handler for help
    dp.add_handler(CommandHandler('help', help))

    # Add conversation handler for querying bot
    # conv_handler = ConversationHandler(
    #     entry_points=[CommandHandler('find', find)],
    #     states={
    #         1 : MessageHandler()
    #     }
    # )
    
    # dp.add_handler(conv_handler)

    updater.start_polling()

if __name__ == '__main__':
    main()