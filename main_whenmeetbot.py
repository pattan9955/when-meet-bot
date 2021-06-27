from datetime import datetime, timezone
# import logging
# from secret_token import TOKEN
import pyrebase
import os

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters

# from secret_token import DB_TOKEN, TOKEN #local secret.py file
from findtimes import *

# For deployment
DB_TOKEN = os.environ.get("DB_TOKEN")
TOKEN = os.environ.get("TOKEN")
PORT = os.getenv('PORT', default=8000)

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

# Configure logger
# logging.basicConfig()

def start(update, context):
    welcome = '''Ohayo minasan! Welcome to WhenMeetBot!\nFor help/tasukete, type '/help'.\nTo upload your .ics file, type '/upload'.\nTo query for common free times, type '/find'.'''
    context.bot.send_message(
        text=welcome,
        chat_id=update.message.chat_id
    )

def help(update, context):
    chat_type = update.message.chat.type
    help_group = "To use the bot, add bot-chan to a group chat, and have all members use '/upload' to upload their .ics files!\n To query for common free times, use '/find'\nTo clear your uploaded file, use '/clear'...baka :3"
    help_private = "To use the bot, use /upload to upload the files that you want to compare.\nTo query for common free times, use '/find'.\nTo clear uploaded files, use '/clear'\nTo cancel at any point of time during uploading or querying, use '/cancel'...baka :3"
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

def view(update, context):
    chat_type = update.message.chat.type
    
    # If command called in PM
    if chat_type == 'private':
        userid = update.message.chat_id
        files = db.child('private').child(userid).child('files').get().val()

        # Check if files are empty
        if not files:
            msg = 'B-b-baka you have nothing inside me now >:( UwU'
            context.bot.send_message(
                text=msg,
                chat_id=userid
            )
        
        # When files are not empty
        res = ""
        for k,v in files.items():
            currentfile = "{} | {}\n".format(k, v['datecreated'])
            res += currentfile
        
        # Display result
        context.bot.send_message(
            text="UwU you currently have these in me:\n{}".format(res),
            chat_id=userid
        )

    # Case for group
    elif chat_type == 'group' or chat_type  == 'supergroup':
        groupid = update.message.chat_id

        files = db.child('group').child(groupid).child('users').get().val()

        # Deal with case where no one has uploads
        if not files:
            msg = 'B-b-baka you have nothing inside me now >:( UwU'
            context.bot.send_message(
                text=msg,
                chat_id=groupid
            )

        # Case with files
        res = ""
        for userid, entry in files.items():
            username = update.message.chat.get_member(userid).user.username
            fullname = update.message.chat.get_member(userid).user.full_name
            date_updated = entry['dateupdated']
            final_entry = "{} ({}) | Updated: {}\n".format(fullname, username, date_updated)
            res += final_entry
        
        # Display result
        context.bot.send_message(
            text="UwU you currently have these in me:\n{}".format(res),
            chat_id=groupid
        )

    # Dealing with channel    
    else:
        msg = 'Gomenasorry bot-chan no work with channel OwO'
        context.bot.send_message(
            text=msg,
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

        # db.child('private').child(user_id).remove()
        files = db.child('private').child(user_id).child('files').get().val()
        
        # Case where no files exist
        if not files:
            no_file_prompt = 'Aight listen up here son you ain\'t got nothin in me ay'
            context.bot.send_message(
                text=no_file_prompt,
                chat_id=user_id
            )
            return ConversationHandler.END

        # Case where files exist
        else:
            button_names = []
            temp = [k for k,v in files.items()]
            for filename in temp:
                filedate = db.child('private').child(user_id).child('files').child(filename).child('datecreated').get().val()
                button_names.append('{} | {}'.format(filename, filedate))

            # Generate keyboard with each filename
            keyboard = generate_clear_keyboard(button_names, 2)

            prompt = "Click filename to delete file. Click 'Clear All' to clear all. Click 'Done' if you're done .______."
            context.bot.send_message(
                text=prompt,
                chat_id=user_id,
                reply_markup = ReplyKeyboardMarkup(keyboard=keyboard)
            )
            return 68
            
    else:
        group_id = update.message.chat_id
        user_id = update.message.from_user.id

        db.child('group').child(group_id).child('users').child(user_id).remove()

        remove_text = "Y-y-you removed your data from bot-chan's storage?! I-it's not like I care...baka"
        context.bot.send_message(
            text=remove_text,
            chat_id=user_id if chat_type == 'private' else group_id
        )

        return ConversationHandler.END

def clear_files(update, context):
    user_input = update.message.text.split(" | ")[0]
    userid = update.message.chat_id
    
    # Case where files still left
    temp_filenamelist = db.child('private').child(userid).child('files').get().val()
    filenamelist = [k for k,v in temp_filenamelist.items()]

    # Check if user wants to clear all
    if user_input.lower() == 'clear all':
        db.child('private').child(userid).child('files').remove()
        context.bot.send_message(
            text='Everything iz kil',
            chat_id=userid,
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    # Check if user_input is valid
    elif user_input not in filenamelist:
        invalid_prompt = "B-b-baka! {} wakaranai desu yo UwU try again kudasai".format(user_input)
        context.bot.send_message(
            text=invalid_prompt,
            chat_id=userid
        )
        return 68
    
    # For valid user input 
    else:
        # Remove file
        db.child('private').child(userid).child('files').child(user_input).remove()
        
        # Check if no files left
        post_remove_list = db.child('private').child(userid).child('files').get().val()
        if not post_remove_list:
            context.bot.send_message(
                text="Everything iz kil",
                chat_id=userid,
                reply_markup=ReplyKeyboardRemove()
            )
            return ConversationHandler.END

        button_names = []
        files = db.child('private').child(userid).child('files').get().val()
        temp = [k for k,v in files.items()]
        for filename in temp:
            filedate = db.child('private').child(userid).child('files').child(filename).child('datecreated').get().val()
            button_names.append('{} | {}'.format(filename, filedate))

        # Regenerate keyboard
        keyboard = generate_clear_keyboard(button_names, 2)

        context.bot.send_message(
            text="{} iz kil\nClick filename to delete file. Click 'Clear All' to clear all. Click 'Done' if you're done .______.".format(user_input),
            chat_id=userid,
            reply_markup=ReplyKeyboardMarkup(keyboard)
        )
        return 68

def generate_clear_keyboard(filenamelist, rowsize):
    keyboard = []
    rowcnt = 0
    row = []
    for button in filenamelist:
        row.append(button)
        if rowcnt < rowsize:
            rowcnt += 1
        else:
            rowcnt = 0
            keyboard.append(copy.copy(row))
            row = []
    if len(row) != 0:
        keyboard.append(copy.copy(row))
    keyboard.append(['Clear All', 'Done'])

    return keyboard

def clear_reprompt(update, context):
    reprompt_text = 'Plz no torture our bot owo tell bot-chan which file you want to delete....baka >w<'
    context.bot.send_message(
        text=reprompt_text,
        chat_id=update.message.chat_id
    )
    return 68

def find(update, context):
    # Check if query done from group or PM with bot
    chat_type = update.message.chat.type
    context.chat_data['included'] = []
    context.chat_data['name_id_map'] = {}
    context.chat_data['params'] = {}
    context.chat_data['included_filenames'] = []

    # Query from group chat
    if chat_type == 'group' or chat_type == 'supergroup':
        group_id = update.message.chat_id

        # Get from db a list of all userIDs for the group
        raw_user_ids = db.child('group').child(group_id).child('users').get().val()

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

            context.chat_data['name_id_map'][final_name] = userid
            row.append(final_name)
            if rowcnt < 2:
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
        files = db.child('private').child(userid).child('files').get().val()
        # print(files)
        temp_filenames = [k for k,v in files.items()]
        
        for filename in temp_filenames:
            filedate = db.child('private').child(userid).child('files').child(filename).child('datecreated').get().val()
            context.chat_data['included_filenames'].append('{} | {}'.format(filename, filedate))

        # If entry doesn't exist
        if not context.chat_data['included_filenames']:
            prompt_upload = "OwO bot-chan couldn't find data :( Use '/upload' first uwu....b-b-baka"
            context.bot.send_message(
                text=prompt_upload,
                chat_id=userid
            )
            return ConversationHandler.END
        
        keyboard = generate_keyboard_from_userlist(context.chat_data['included_filenames'], 2)

        prompt = "UwU you want to find common free times? Tell bot-chan which files you want to include...baka >w<"
        context.bot.send_message(
            text=prompt,
            chat_id=update.message.chat_id,
            reply_markup=ReplyKeyboardMarkup(keyboard=keyboard)
        )
        return 1

    # Query through channel
    else:
        context.bot.send_message(
            text="bot-chan no worku with channels now...baka >w<",
            chat_id=update.message.chat_id
        )
        return ConversationHandler.END

def generate_keyboard_from_userlist(userlist, rowsize):
    keyboard = []
    rowcnt = 0
    row = []
    for user in userlist:
        row.append(user)
        if rowcnt < rowsize:
            rowcnt += 1
        else:
            rowcnt = 0
            keyboard.append(copy.copy(row))
            row = []
    if len(row) != 0:
        keyboard.append(copy.copy(row))
    keyboard.append(['Done', 'Cancel'])

    return keyboard

def find_persons_to_query(update, context):
    user_selection = update.message.text
    group_id = update.message.chat.id
    chat_type = update.message.chat.type

    if chat_type == 'private':
        # User done selecting files
        if user_selection == 'Done':
            prompt_time = "Oki uwu now plz gib bot-chan a start date to search from e.g. '01/01/2021 15:00' for 3pm on 1 Jan 2021"
            context.bot.send_message(
                text=prompt_time,
                chat_id=update.message.chat_id,
                reply_markup=ReplyKeyboardRemove()
            )
            return 2

        # Check if user input in saved chat_data
        elif user_selection not in context.chat_data['included_filenames']:
            reprompt = "B-b-baka...nani kore is this bot-chan no understando try again plz"
            context.bot.send_message(
                text=reprompt,
                chat_id=update.message.chat_id
            )
            return 1

        # Valid user input
        else:
            # Parse user input for file name
            filename = user_selection.split(' | ')[0]

            # Pop user_selection from chat_data
            context.chat_data['included_filenames'].remove(user_selection)

            # Add icalrep for given filename to included
            icalrep = db.child('private').child(group_id).child('files').child(filename).child('icalrep').get().val()
            context.chat_data['included'].append(icalrep)

            # Check if files left
            files_left = context.chat_data['included_filenames']

            if files_left:
                keyboard = generate_keyboard_from_userlist(files_left, 2)
                prompt_for_next = "Ara ara~ bot-chan has included {} >w< Tell bot-onee-chan what else you want to include :3".format(user_selection)
                context.bot.send_message(
                    text=prompt_for_next,
                    chat_id=group_id,
                    reply_markup=ReplyKeyboardMarkup(keyboard=keyboard)
                )
                return 1

            # No users left
            else:
                prompt_for_next = "Ara ara~ Bot-chan sees you've added all your files already >:) Give bot-onee-chan a start date to search from e.g. '01/01/2021 15:00' for 3pm on 1 Jan 2021"
                context.bot.send_message(
                    text=prompt_for_next,
                    chat_id=group_id,
                    reply_markup=ReplyKeyboardRemove()
                )
                return 2

    else:
        # User done selecting users
        if user_selection == 'Done':
            prompt_time = "Oki uwu now plz gib bot-chan a start date to search from e.g. '01/01/2021 15:00' for 3pm on 1 Jan 2021"
            context.bot.send_message(
                text=prompt_time,
                chat_id=update.message.chat_id,
                reply_markup=ReplyKeyboardRemove()
            )
            return 2

        # Check if username in saved chat_data
        elif user_selection not in context.chat_data['name_id_map'].keys():
            reprompt = "B-b-baka...nani kore is this bot-chan no understando try again plz"
            context.bot.send_message(
                text=reprompt,
                chat_id=update.message.chat_id
            )
            return 1

        # Definitely valid user input
        else:
            # Retrieve user_id from username and remove user from mapping
            user_id = context.chat_data['name_id_map'].pop(user_selection)

            # Update included ics files
            ics_str = db.child('group').child(group_id).child('users').child(user_id).child('icalrep').get().val()
            context.chat_data['included'].append(ics_str)

            # Generate new keyboard from remaining users
            users_left = list(context.chat_data['name_id_map'].keys())
            
            # Users left
            if users_left:
                keyboard = generate_keyboard_from_userlist(users_left, 2)
                prompt_for_next = "Ara ara~ bot-chan has included {} >w< Tell bot-onee-chan who else you want to include :3".format(user_selection)
                context.bot.send_message(
                    text=prompt_for_next,
                    chat_id=group_id,
                    reply_markup=ReplyKeyboardMarkup(keyboard=keyboard)
                )
                return 1

            # No users left
            else:
                prompt_for_next = "Ara ara~ Bot-chan sees you've added all your friends already >:) Give bot-onee-chan a start date to search from e.g. '01/01/2021 15:00' for 3pm on 1 Jan 2021"
                context.bot.send_message(
                    text=prompt_for_next,
                    chat_id=group_id,
                    reply_markup=ReplyKeyboardRemove()
                )
                return 2

def cancel_find(update, context):
    cancel_text = "Bot-chan cancelled your request...d-d-don't get me wrong, it's not like I want you to use me again...baka"
    context.bot.send_message(
        text=cancel_text,
        chat_id=update.message.chat_id,
        reply_markup=ReplyKeyboardRemove() 
    )
    return ConversationHandler.END

def find_start_time(update, context):
    user_input = update.message.text
    try:
        parsed_date = datetime.strptime(user_input, "%d/%m/%Y %H:%M")
        context.chat_data['params']['start'] = parsed_date
        prompt_end_time = "Yare yare daze bot-chan has a start time now OwO Gib me owari no toki >w< e.g. '01/01/2021 15:00' for 3pm on 1 Jan 2021\nTo tell bot-chan yamete kudasai, type '/cancel'"
        context.bot.send_message(
            text=prompt_end_time,
            chat_id=update.message.chat_id
        )
        return 3

    except ValueError:
        error_prompt = "B-b-baka! {} wakaranai desu yo UwU try again kudasai".format(user_input)
        context.bot.send_message(
            text=error_prompt,
            chat_id=update.message.chat_id
        )
        return 2

def find_end_time(update, context):
    user_input = update.message.text
    try:
        parsed_date = datetime.strptime(user_input, "%d/%m/%Y %H:%M")
        context.chat_data['params']['end'] = parsed_date
        prompt_end_time = "Yare yare daze bot-chan has an end time now OwO Tell bot-onee-san how much free time you need >w< e.g. '2' for minimum 2 hour blocks of free time\nBot-chan only supports intervals up to 24 for now UwU\nTo tell bot-chan yamete kudasai, type '/cancel'"
        context.bot.send_message(
            text=prompt_end_time,
            chat_id=update.message.chat_id
        )
        return 4

    except ValueError:
        error_prompt = "B-b-baka! {} wakaranai desu yo UwU try again kudasai".format(user_input)
        context.bot.send_message(
            text=error_prompt,
            chat_id=update.message.chat_id
        )
        return 3

def process_result(res_dict):
    final = ""
    for day,times in res_dict.items():
        intermediate = ""
        intermediate += day
        intermediate += ':\n'

        for time in times:
            start = time[0] % 24
            end = time[1] % 24
            if start < 10:
                start = '0{}00'.format(start)
            else:
                start = '{}00'.format(start)

            if end < 10:
                end = '0{}00'.format(end)
            else:
                end = '{}00'.format(end)
            intermediate += '    {}hrs - {}hrs\n'.format(start, end)
        
        if intermediate == '{}:\n'.format(day):
            continue
        final += intermediate
        final += '\n'

    return final

def find_min_interval(update, context):
    user_input = update.message.text

    try:
        parsed_interval = int(user_input)
        if parsed_interval > 24 or parsed_interval <= 0:
            raise ValueError
        context.chat_data['params']['interval'] = parsed_interval
        result = process_result(find_free_time(context.chat_data['included'], context.chat_data['params']['start'], context.chat_data['params']['end'], context.chat_data['params']['interval']))
        result = "No free time :'(" if (result == "") else result
        context.bot.send_message(
            text=result,
            chat_id=update.message.chat_id
        )
        return ConversationHandler.END
    except ValueError:
        error_prompt = "Blimey! You must have made a mistake you nimwit! What is {}? Utter bollocks! Try again!".format(user_input)
        context.bot.send_message(
            text=error_prompt,
            chat_id=update.message.chat_id
        )
        return 4

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
        upload_text = "I-it's not like I need your .ics files b-b-baka! Upload your .ics files thenk or use '/cancel' to cancel"
        context.bot.send_message(
            text=upload_text,
            chat_id=update.message.chat_id
        )
        return 1

    # Case for group chat
    else:
        # print(db.child('group').child(group_id).child(user_id).get().val())
        # Check if ics file for this user already exists in db
        if db.child('group').child(group_id).child('users').child(user_id).child('icalrep').get().val() != None:
            # print('Prompt group overwrite')
            date = db.child('group').child(group_id).child('users').child(user_id).child('dateupdated').get().val()
            prompt = "B-b-baka, you have an .ics in me already uploaded on {}...send 'yes' to overwrite or 'no' to cancel".format(date)
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

def on_doc_upload(update, context):    
    group_id = update.message.chat_id
    user_id = update.message.from_user.id
    doc = update.message.document
    fileid = update.message.document.file_id
    filename = update.message.document.file_name.replace('.', '_')
    chat_dt = str(aslocaltimestr(update.message.date))
    is_PM = True if update.message.chat.type == 'private' else False
    content = ""

    # Download the document and populate content string
    with open("{}".format(fileid), 'wb') as f:
        context.bot.get_file(doc).download(out = f)
    
    with open("{}".format(fileid), encoding="latin-1") as f:
        for line in f:
            content += line
    os.remove('{}'.format(fileid))

    if is_PM:
        db.child('private').child(user_id).child('files').update({filename:{'icalrep':content, 'datecreated':chat_dt}})

    else:
        db.child('group').child(group_id).child('users').child(user_id).update({'icalrep':content, 'dateupdated':chat_dt})

    confirmation = "UwU bot-chan has successfully uploaded {}'s file...baka".format(update.message.from_user.username)
    context.bot.send_message(
        text=confirmation,
        chat_id=group_id
    )

    return ConversationHandler.END

def error(update, context):
    print(context.error)
    context.bot.send_message(
        text="ERROR! Bot-chan itai! Plz don't do that kudasai ><",
        chat_id = update.message.chat_id,
        reply_markup = ReplyKeyboardRemove()
    )

def aslocaltimestr(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None).strftime('%Y/%m/%d %H:%M')

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher;

    # Add command handler for initializing bot
    dp.add_handler(CommandHandler('start', start))

    # Add commmand handler for help
    dp.add_handler(CommandHandler('help', help))

    # Add command handler for clear
    delete_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('clear', clear)],
        states={
            68 : [MessageHandler(Filters.regex('(?i)^Done$'), cancel_find), CommandHandler('cancel', cancel_find), MessageHandler(Filters.text, clear_files)]
        },
        fallbacks=[MessageHandler(~Filters.text, clear_reprompt), CommandHandler('cancel', cancel_find)]
    )
    dp.add_handler(delete_conv_handler)

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
            1 : [CommandHandler("cancel", cancel_find), MessageHandler(Filters.regex('(?i)^Cancel$'), cancel_find), MessageHandler(Filters.text, find_persons_to_query)],
            2 : [CommandHandler("cancel", cancel_find), MessageHandler(Filters.text, find_start_time)],
            3 : [CommandHandler("cancel", cancel_find), MessageHandler(Filters.text, find_end_time)],
            4 : [CommandHandler("cancel", cancel_find), MessageHandler(Filters.text, find_min_interval)]
        },
        fallbacks=[CommandHandler('cancel', cancel_find)]
    )
    dp.add_handler(query_conv_handler)

    # Add command handler for view
    dp.add_handler(CommandHandler('view', view))

    # Add error handler for bot
    dp.add_error_handler(error)

    # updater.start_polling()
    updater.start_webhook(port=PORT)

if __name__ == '__main__':
    main()