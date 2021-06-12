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
    welcome = '''Ohayo minasan! Welcome to WhenMeetBot!\nFor help/tasukete, type '/help'.\nTo upload your .ics file, type '/upload'.\nTo query for common free times, type '/find'.'''
    context.bot.send_message(
        text=welcome,
        chat_id=update.message.chat_id
    )

def help(update, context):
    chat_type = update.message.chat.type
    help_group = "To use the bot, add bot-chan to a group chat, and have all members use '/upload' to upload their .ics files!\n To query for common free times, use '/find'\nTo clear your uploaded file, use '/clear'...baka :3"
    help_private = "To use the bot, use /upload to upload the files that you want to compare.\nTo query for common free times, use '/find'.\nTo clear all uploaded files, use '/clear'...baka :3"
    if chat_type == 'private':
        context.bot.send_message(
            text=help_private,
            chat_id=update.message.chat_id
        )

    else:
        context.bot.send_message(
            text=help_group,
            chat_id=update.message.chat_id
        )

def cancel_upload(update, context):
    text = 'upload iz kil'
    context.bot.send_message(
        text=text,
        chat_id=update.message.chat_id
    )
    return ConversationHandler.END

def clear(update, context):
    chat_type = update.message.chat.type
    if chat_type == 'private':
        user_id = update.message.chat_id

        db.child('private').child(user_id).remove()

    else:
        group_id = update.message.chat_id
        user_id = update.message.from_user.id

        db.child('group').child(group_id).child(user_id).remove()

    remove_text = "Y-y-you removed your data from bot-chan's storage?! I-it's not like I care...baka"
    context.bot.send_message(
        text=remove_text,
        chat_id=group_id
    )

def find(update, context):
    # Check if query done from group or PM with bot
    chat_type = update.message.chat.type
    context.chat_data['included'] = []

    # Query from group chat
    if chat_type == 'group' or chat_type == 'supergroup':
        group_id = update.message.chat_id

        # Get from db a list of all userIDs for the group
        raw_user_ids = db.child('group').child(group_id).get().val()

        # Check if user_ids is empty
        if not raw_user_ids:
            prompt_upload = "OwO bot-chan couldn't find data :( Use '/upload' first uwu....b-b-baka"
            context.bot.send_message(
                text=prompt_upload,
                chat_id = group_id
            )
            return ConversationHandler.END

        user_ids = list(raw_user_ids.keys())

        # Populate keyboard buttons with names of users
        keyboard = []
        rowcnt = 0
        row = []
        for userid in user_ids:
            username = update.message.chat.get_member(userid).user.username
            fullname = update.message.chat.get_member(userid).user.full_name
            final_name = "{} ({})".format(fullname, username)

            context.chat_data[final_name] = userid
            
            if rowcnt < 3:
                row.append(final_name)
                rowcnt += 1
            else:
                rowcnt = 0
                keyboard.append(copy.copy(row))
                row = []
            
        if len(row) != 0:
            keyboard.append(copy.copy(row))
        keyboard.append(['Done', 'Cancel'])

        prompt = "UwU you want to find common free times? Tell bot-chan who you want to include...baka >w<"
        context.bot.send_message(
            text=prompt,
            chat_id=update.message.chat_id,
            reply_markup=ReplyKeyboardMarkup(keyboard=keyboard)
        )
        return 1

    # Query through PM with bot
    elif chat_type == "private":
        userid = update.message.chat_id

        # Check if entry exists in db
        data = db.child('private').child(userid).get().val()
        
        # If entry doesn't exist
        if not data:
            prompt_upload = "OwO bot-chan couldn't find data :( Use '/upload' first uwu....b-b-baka"
            context.bot.send_message(
                text=prompt_upload,
                chat_id=userid
            )
            return ConversationHandler.END
        
        context.chat_data['included'].extend(data)

        start_time_prompt = ">w< bot-chan found your ics file uwu plz gib bot-chan a start date to search from e.g. '2021-01-01' for 1 Jan 2021"
        context.bot.send_message(
            text=start_time_prompt,
            chat_id=userid
        )
        return 2

    # Query through channel
    else:
        context.bot.send_message(
            text="bot-chan no worku with channels now...baka >w<",
            chat_id=update.message.chat_id
        )
        return ConversationHandler.END

#TODO
def find_persons_to_query(update, context):
    user_selection = update.message.text

    # # Not valid user input
    # if not user_selection:
    #     reprompt = "B-b-baka...nani kore is this bot-chan no understando try again plz"
    #     context.bot.send_message(
    #         text=reprompt,
    #         chat_id=update.message.chat_id
    #     )
    #     return 1

    # User done selecting users
    if user_selection == 'Done':
        prompt_time = "Oki uwu now plz gib bot-chan a start date to search from e.g. '2021-01-01' for 1 Jan 2021"
        context.bot.send_message(
            text=prompt_time,
            chat_id=update.message.chat_id,
            reply_markup=ReplyKeyboardRemove()
        )
        return 2

    # Possibly valid user input i.e. string of form xxx(xxx)
    # Check if username in saved chat_data
    elif user_selection not in context.chat_data.keys():
        reprompt = "B-b-baka...nani kore is this bot-chan no understando try again plz"
        context.bot.send_message(
            text=reprompt,
            chat_id=update.message.chat_id
        )
        return 1

    # Definitely valid user input
    else:
        # Retrieve user_id from username
        user_id = context.chat_data.pop(user_selection)

def cancel_find(update, context):
    cancel_text = "Bot-chan cancelled your request...d-d-don't get me wrong, it's not like I want you to use me again...baka"
    context.bot.send_message(
        text=cancel_text,
        chat_id=update.message.chat_id,
        reply_markup=ReplyKeyboardRemove() 
    )
    return ConversationHandler.END

#TODO
def find_start_time(update, context):
    pass

#TODO
def find_end_time(update, context):
    pass

#TODO
def find_min_interval(update, context):
    pass

#TODO
def display_result(update, context):
    pass

#TODO
def upload(update, context):
    group_id = update.message.chat_id
    user_id = update.message.from_user.id
    chat_type = update.message.chat.type

    if chat_type == "channel":
        prompt = "Ara ara~ Channel wa dame desu yo"
        context.bot.send_message(
            text=prompt,
            chat_id=group_id
        )

    is_PM = False if chat_type == "group" or chat_type == "supergroup" else True

    # Case for PM
    if is_PM:
        # # Check if ics file for this user already exists in db
        # if db.child('private').child(user_id).get().val() != None:
        #     prompt = "B-b-baka, you have a .ics in me already owo...send 'yes' to overwrite or 'no' to cancel"
        #     context.bot.send_message(
        #         text=prompt,
        #         chat_id=group_id
        #     )
        #     return 2

        upload_text = "I-it's not like I need your .ics files b-b-baka! Upload your .ics files thenk or use '/cancel' to cancel"
        context.bot.send_message(
            text=upload_text,
            chat_id=update.message.chat_id
        )
        return 1

    # Case for group chat
    else:
        print(db.child('group').child(group_id).child(user_id).get().val())
        # Check if ics file for this user already exists in db
        if db.child('group').child(group_id).child(user_id).get().val() != None:
            print('Prompt group overwrite')
            prompt = "B-b-baka, you have a .ics in me already owo...send 'yes' to overwrite or 'no' to cancel"
            context.bot.send_message(
                text=prompt,
                chat_id=group_id
            )
            return 2

        upload_text = "I-it's not like I need your .ics files b-b-baka! Upload your .ics files thenk or use '/cancel' to cancel"
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

def upload_not_understood(update, context):
    text = "I no understando, zen zen wakaranai...baka...\nSend 'yes' to overwrite or 'no' to cancel"
    context.bot.send_message(
        text=text,
        chat_id=update.message.chat_id
    )
    return 2

#TODO
def start_not_understood(update, context):
    pass

#TODO
def end_not_understood(update, context):
    pass

#TODO
def interval_not_understood(update, context):
    pass

#TODO
def on_doc_upload(update, context):
    # # Check if message sent from group. If not, prompt user to add bot to group
    # if update.message.chat.type != "group" and update.message.chat.type  != "supergroup":
    #     text = "Add bot-chan to group uwu before upload...baka"
    #     context.bot.send_message(
    #         text=text,
    #         chat_id=update.message.chat_id
    #     )
    #     return 1
    
    group_id = update.message.chat_id
    user_id = update.message.from_user.id
    doc = update.message.document
    fileid = update.message.document.file_id
    is_PM = True if update.message.chat.type == 'private' else False
    content = ""

    # Download the document and populate content string
    with open("{}".format(fileid), 'wb') as f:
        context.bot.get_file(doc).download(out = f)
    
    with open("{}".format(fileid)) as f:
        for line in f:
            content += line
    os.remove('{}'.format(fileid))

    if is_PM:
        current_len = db.child('private').child(user_id).get().val()
        if not current_len:
            current_len = 0
        else:
            current_len = len(current_len)
        db.child('private').child(user_id).child(current_len).set(content)
        print('Added private + {}'.format(current_len))

    else:
        # Write ics file to database if no entry for user present
        if db.child('group').child(group_id).child(user_id).get().val() == None:
            db.child('group').child(group_id).child(user_id).set(content)
            # print('Added group')

        # Otherwise update the file if entry for user already present
        else:
            db.child('group').child(group_id).update({user_id : content})
            # print('Updated group')

    

    confirmation = "UwU bot-chan has successfully uploaded {}'s file...baka".format(update.message.from_user.username)
    context.bot.send_message(
        text=confirmation,
        chat_id=group_id
    )

    return ConversationHandler.END

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher;

    # Add command handler for initializing bot
    dp.add_handler(CommandHandler('start', start))

    # Add commmand handler for help
    dp.add_handler(CommandHandler('help', help))

    # Add command handler for clear
    dp.add_handler(CommandHandler('clear', clear))

    # Add conversation handler for uploading document
    upload_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('upload', upload)],
        states={
            1 : [MessageHandler(Filters.document.file_extension("ics"), on_doc_upload), CommandHandler('cancel', cancel_upload)],
            2 : [MessageHandler(Filters.regex('(?i)^yes$|^no$'), ask_confirmation), MessageHandler(~Filters.regex('(?i)^yes$|^no$'), upload_not_understood)]
        },
        fallbacks=[MessageHandler(~Filters.document.file_extension("ics"), reprompt), CommandHandler('cancel', cancel_upload)]
    )
    dp.add_handler(upload_conv_handler)

    # Add conversation handler for querying bot
    query_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('find', find)],
        states={
            1 : [MessageHandler(Filters.regex('(?i)^Cancel$'), cancel_find), MessageHandler(Filters.text, find_persons_to_query)],
            2 : [MessageHandler(Filters.text, find_start_time), MessageHandler(Filters.text, start_not_understood), CommandHandler("cancel", cancel_find)],
            3 : [MessageHandler(Filters.text, find_end_time), MessageHandler(Filters.text, end_not_understood), CommandHandler("cancel", cancel_find)],
            4 : [MessageHandler(Filters.text, find_min_interval), MessageHandler(Filters.text, interval_not_understood), CommandHandler("cancel", cancel_find)],
            5 : [MessageHandler(Filters.text, display_result)]
        },
        fallbacks=[CommandHandler('cancel', cancel_find)]
    )
    dp.add_handler(query_conv_handler)

    updater.start_polling()

if __name__ == '__main__':
    main()