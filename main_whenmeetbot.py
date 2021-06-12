from datetime import datetime
import pyrebase
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters, updater

from secret_token import DB_TOKEN, TOKEN #local secret.py file
from findtimes import *

URL = "https://api.telegram.org/bot{}/".format(TOKEN)

# Connect to Firebase db
config = {
    "apiKey": "{}".format(DB_TOKEN),
    "authDomain": "whenmeetbot.firebaseapp.com",
    "databaseURL": "https://whenmeetbot-default-rtdb.asia-southeast1.firebasedatabase.app",
    "storageBucket": "whenmeetbot.appspot.com"
}
firebase = pyrebase.initialize_app(config)
db = firebase.database()

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

def cancel_upload(update, context):
    text = 'upload iz kil'
    context.bot.send_message(
        text=text,
        chat_id=update.message.chat_id
    )
    return ConversationHandler.END

#TODO
def find(update, context):
    pass

#TODO
def find_persons_to_query(update, context):
    pass

#TODO
def cancel_find(update, context):
    pass

#TODO
def find_start_time(update, context):
    pass

#TODO
def find_end_time(update, context):
    pass

#TODO
def find_min_interval(update, context):
    pass

def upload(update, context):
    group = update.message.chat_id
    user = update.message.from_user.id

    # Check if ics file for this user already exists in db
    if db.child(group).child(user).get().val() != None:
        prompt = "B-b-baka, you have a .ics in me already owo...send 'yes' to overwrite or 'no' to cancel"
        context.bot.send_message(
            text=prompt,
            chat_id=group
        )
        return 2

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

def ask_confirmation(update, context):
    msg = update.message.text
    if msg == 'yes':
        upload_text = 'Plz send .ics files thenk or use "/cancel" to cancel'
        context.bot.send_message(
            text=upload_text,
            chat_id=update.message.chat_id
        )
        return 1
    else:
        context.bot.send_message(
            text='Upload iz kil',
            chat_id=update.message.chat_id
        )
        return ConversationHandler.END

def not_understood(update, context):
    text = "I no understando, zen zen wakaranai...baka...\nSend 'yes' to overwrite or 'no' to cancel"
    context.bot.send_message(
        text=text,
        chat_id=update.message.chat_id
    )
    return 2

def on_doc_upload(update, context):
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

    # Write ics file to database if no entry for user present
    if db.child(group).child(user).get().val() == None:
        db.child(group).child(user).set(content)
        # print('Added')

    # Otherwise update the file if entry for user already present
    else:
        db.child(group).update({user : content})
        # print('Updated')

    confirmation = "UwU bot-chan has successfully uploaded {}'s file...baka".format(update.message.from_user.username)
    context.bot.send_message(
        text=confirmation,
        chat_id=group
    )

    return ConversationHandler.END

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
            1 : [MessageHandler(Filters.document.file_extension("ics"), on_doc_upload), CommandHandler('cancel', cancel_upload)],
            2 : [MessageHandler(Filters.regex('(?i)^yes$|^no$'), ask_confirmation), MessageHandler(~Filters.regex('(?i)^yes$|^no$'), not_understood)]
        },
        fallbacks=[MessageHandler(~Filters.document.file_extension("ics"), reprompt), CommandHandler('cancel', cancel_upload)]
    )
    dp.add_handler(upload_conv_handler)

    # Add conversation handler for querying bot
    query_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('find', find)],
        states={
            1 : [MessageHandler(Filters.text, find_persons_to_query), CommandHandler("cancel", cancel_find)],
            2 : [MessageHandler(Filters.text, find_start_time), CommandHandler("cancel", cancel_find)],
            3 : [MessageHandler(Filters.text, find_end_time), CommandHandler("cancel", cancel_find)],
            4 : [MessageHandler(Filters.text, find_min_interval), CommandHandler("cancel", cancel_find)],
        },
        fallbacks=[CommandHandler('cancel', cancel_find)]
    )
    dp.add_handler(query_conv_handler)

    updater.start_polling()

if __name__ == '__main__':
    main()