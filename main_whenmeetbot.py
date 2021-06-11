import json
import requests
import time
import telegram
import pyrebase
import os

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

def start(update, context):
    welcome = '''Welcome to WhenMeetBot!\nFor help, type '/help'.\nTo upload your .ics file, type '/upload'.\nTo query for common free times, type '/find'.'''
    context.bot.send_message(
        text=welcome,
        chat_id=update.message.chat_id
    )
    
def help(update, context):
    help = "To use the bot, add the bot to a group chat, and have all members use '/upload' to upload their .ics files!\n To query for common free times, use '/find' :D"
    context.bot.send_message(
        text=help,
        chat_id=update.message.chat_id
    )

def cancel(update, context):
    text = 'upload iz kil'
    context.bot.send_message(
        text=text,
        chat_id=update.message.chat_id
    )
    return ConversationHandler.END

#TODO
def find(update, context):
    pass

def upload(update, context):
    upload_text = 'Plz send .ics files thenk or use "/cancel" to cancel'
    context.bot.send_message(
        text=upload_text,
        chat_id=update.message.chat_id
    )
    return 1

def reprompt(update, context):
    reprompt_text = 'Plz no torture our bot owo send proper .ics file pls....baka >w<'
    context.bot.send_message(
        text=reprompt_text,
        chat_id=update.message.chat_id
    )
    return 1

#TODO
def onDocUpload(update, context):
    # # Check if message sent from group. If not, prompt user to add bot to group
    # if update.message.chat.type != "group" and update.message.chat.type  != "supergroup":
    #     text = "Add bot-chan to group uwu before upload...baka"
    #     context.bot.send_message(
    #         text=text,
    #         chat_id=update.message.chat_id
    #     )
    #     return 1
    
    group = update.message.chat_id
    user = update.message.from_user.id
    doc = update.message.document
    fileid = update.message.document.file_id
    content = ""

    # Download the document and populate content string
    with open("{}".format(fileid), 'wb') as f:
        context.bot.get_file(doc).download(out = f)
    
    with open("{}".format(fileid)) as f:
        for line in f:
            content += line
    os.remove('{}'.format(fileid))

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher;

    # Add command handler for initializing bot
    dp.add_handler(CommandHandler('start', start))

    # Add commmand handler for help
    dp.add_handler(CommandHandler('help', help))

    # Add conversation handler for uploading document
    upload_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('upload', upload)],
        states={
            1 : [MessageHandler(Filters.document.file_extension("ics"), onDocUpload), CommandHandler('cancel', cancel)]
        },
        fallbacks=[MessageHandler(~Filters.document.file_extension("ics"), reprompt), CommandHandler('cancel', cancel)]
    )
    dp.add_handler(upload_conv_handler)

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