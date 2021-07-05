from datetime import datetime, timezone
from telegram.ext.callbackqueryhandler import CallbackQueryHandler

from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters

# For testing purposes
# from secret_token import TEST_TOKEN, DB_TOKEN

import pyrebase
import os

# from secret_token import DB_TOKEN, TOKEN #local secret.py file
from findtimes import *    

# Constants for bot
(
    HELP,
    FAQ_SELECTION,
    FAQ_PURPOSE_SELECTOR,
    FAQ_COMMAND_SELECTOR,
    FAQ_EXPORT,
    CLEAR,
    CLEAR_FILES,
    FIND,
    VIEW,
    UPLOAD,
    ON_DOC_UPLOAD,
    ASK_CONFIRMATION,
    SELECTION,
    FIND_PERSONS,
    FIND_START,
    FIND_END,
    FIND_INT,
    END
) = map(chr, range(18))

# For deployment
DB_TOKEN = os.environ.get("DB_TOKEN")
TOKEN = os.environ.get("TOKEN")
# PORT = os.getenv('PORT', default=88)

# For testing
# TOKEN = TEST_TOKEN

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
    buttons = [
        [
            InlineKeyboardButton(text='Help', callback_data=str(HELP)), 
            InlineKeyboardButton(text='View', callback_data=str(VIEW)), 
            InlineKeyboardButton(text='Upload', callback_data=str(UPLOAD))
        ],
        [
            InlineKeyboardButton(text='Find', callback_data=str(FIND)), 
            InlineKeyboardButton(text='Clear', callback_data=str(CLEAR)),
            InlineKeyboardButton(text='Cancel', callback_data=str(END))
        ]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    context.bot.send_message(
        text='Please choose an option!',
        chat_id=update.message.chat_id,
        reply_markup=keyboard
    )
    return SELECTION

def end(update, context):
    query = update.callback_query

    query.answer()

    query.edit_message_text(
        text='Bye! Use /start to interact with me again :)'
    )
    return END

def help(update, context):
    query = update.callback_query
    
    query.answer()
    
    keyboard = [
        [InlineKeyboardButton(text='How does the bot work?', callback_data='PURPOSE')],
        [InlineKeyboardButton(text='How do I an export an .ics file from my calendar app?', callback_data='EXPORT')],
        [InlineKeyboardButton(text='How do I use the commands?', callback_data='COMMAND')],
        [InlineKeyboardButton(text='Cancel', callback_data='END')]
    ]

    query.edit_message_text(
        text='Hi, what do you need help with?',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    return FAQ_SELECTION

def faq_selection(update, context):
    query = update.callback_query
    user_selection = query.data

    query.answer()

    if user_selection == "END":
        query.edit_message_text(
            text='Understood. Use /start to interact with our bot again :)'
        )
        return END
    elif user_selection == "PURPOSE":
        purpose_of_life = ("This bot finds common free times amongst uploaded .ics (calendar) files.\n\n"
        "Group Chat:\n\nEach member uploads their own calendar file. The bot can then find common free times amongst user-specified members.\n\n\n"
        "Private Message:\n\nThe user can upload one or more calendar file(s). The bot can then find common free times amongst user-specified files.\n\n\n"
        "Which usage scenario do you need more information on?") 
        
        keyboard = [
            [InlineKeyboardButton(text="Use in a Group Chat", callback_data="GROUP")],
            [InlineKeyboardButton(text="Use in Private Message", callback_data="PM")],
            [InlineKeyboardButton(text="Cancel", callback_data="END")],
            [InlineKeyboardButton(text="Go Back", callback_data="BACK")]
        ]
        query.edit_message_text(
            text=purpose_of_life,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        return FAQ_PURPOSE_SELECTOR
    elif user_selection == "COMMAND":
        command_help = ("Explanation of basic commands:\n\n"
        "1) View - Lists out all files stored for that particular chat.\n\n"
        "2) Upload - Allows the user to upload a file to the bot. Click the button below for more information.\n\n"
        "3) Find - Searches for common free times amongst selected .ics files/users. Click the button below for more information.\n\n"
        "4) Clear - Deletes previously uploaded files by the user. Click the button below for more information.\n\n")
        
        keyboard = [
            [InlineKeyboardButton(text="How do I use 'Upload'?", callback_data='HELP_UPLOAD')],
            [InlineKeyboardButton(text="How do I use 'Find'?", callback_data='HELP_FIND')],
            [InlineKeyboardButton(text="How do I use 'Clear'?", callback_data="HELP_CLEAR")],
            [InlineKeyboardButton(text="Go back", callback_data="BACK")],
            [InlineKeyboardButton(text="Cancel", callback_data="END")]
        ]
        
        query.edit_message_text(
            text=command_help,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        return FAQ_COMMAND_SELECTOR
    else:
        export_help = ("For help exporting your calendars to .ics files, refer to the links below.\n\n"
        "Samsung Calendar/S Planner -\nhttps://toolbox.iskysoft.com/android-transfer/export-samsung-calendar.html\n\n"
        "Apple Calendar -\nhttps://support.apple.com/en-sg/guide/calendar/icl1023/mac\n\n"
        "Google Calendar -\nhttps://support.google.com/calendar/answer/37111?hl=en\n\n"
        "Outlook Calendar -\nhttps://www.techwalla.com/articles/how-to-convert-an-outlook-calendar-to-ics\n\n\n"
        "To interact with the bot again, use /start :)")

        query.edit_message_text(
            text=export_help
        )
        return END

def faq_purpose_selector(update, context):
    query = update.callback_query
    user_selection = query.data

    query.answer()

    if user_selection == "END":
        query.edit_message_text(
            text="Understood. Use /start to interact with the bot again :)"
        )
        return END
    elif user_selection ==  "BACK":
        keyboard = [
            [InlineKeyboardButton(text='How does the bot work?', callback_data='PURPOSE')],
            [InlineKeyboardButton(text='How do I an export an .ics file from my calendar app?', callback_data='EXPORT')],
            [InlineKeyboardButton(text='How do I use the commands?', callback_data='COMMAND')],
            [InlineKeyboardButton(text='Cancel', callback_data='END')]
        ]

        query.edit_message_text(
            text='Hi, what do you need help with?',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        return FAQ_SELECTION
    elif user_selection == "GROUP":
        group_help = ("Group Chat:\n\n"
        "1) Add the bot to the group.\n\n"
        "2) Get your group members to upload their .ics files to the bot using the 'Upload' button.\n\n"
        "3) After uploading, use the 'Find' button to ask the bot for common free times amongst user-selected members.\n\n"
        "4) Users can choose to delete their uploaded files at any time using the 'Clear' button.\n\n\n"
        "Use /start to interact with the bot again :)")
        
        query.edit_message_text(
            text=group_help
        )
        return END
    else:
        pm_help = ("Private Message:\n\n"
        "1) Upload your .ics files using the 'Upload' button.\n\n"
        "2) After uploading, use the 'Find' button to ask the bot for common free times amongst user-selected files.\n\n"
        "3) Users can choose to delete any or all of their uploaded files at any time using the 'Clear button.\n\n\n"
        "Use /start to interact with the bot again :)")
        
        query.edit_message_text(
            text=pm_help
        )
        return END

def faq_command_selector(update, context):
    query = update.callback_query
    user_selection = query.data

    if user_selection == "END":
        query.edit_message_text(
            text="Understood. Use /start to interact with the bot again :)"
        )
        return END
    elif user_selection == "BACK":
        keyboard = [
            [InlineKeyboardButton(text='How does the bot work?', callback_data='PURPOSE')],
            [InlineKeyboardButton(text='How do I an export an .ics file from my calendar app?', callback_data='EXPORT')],
            [InlineKeyboardButton(text='How do I use the commands?', callback_data='COMMAND')],
            [InlineKeyboardButton(text='Cancel', callback_data='END')]
        ]

        query.edit_message_text(
            text='Hi, what do you need help with?',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        return FAQ_SELECTION
    elif user_selection == "HELP_FIND":
        help_find_text = ("1) This function only works if there are previously uploaded .ics files for that chat (group or PM).\n\n"
        "2) A menu will appear allowing you to select files(in PM) or users(in group chat) that you want to include in your query.\n\n"
        "3) After selecting users/files that you want to include, click the 'Done' button.\n\n"
        "4) The bot will then prompt for a start datetime, followed by an end datetime in DD/MM/YYYY HH:MM format.\n"
        "  > These represent the search interval for the bot, so only free times in this interval will be displayed.\n\n"
        "5) The bot will then ask for an interval (in hours) between 0 to 24.\n"
        "  > This represents the minimum time interval for a block of free time to be considered valid.\n\n"
        "6) Use the 'Cancel' button or the '/cancel' command, whichever is available, to cancel the operation.\n\n\n"
        "Use the /start command to interact with the bot again :)")

        query.edit_message_text(
            text=help_find_text
        )
        return END
    elif user_selection == "HELP_UPLOAD":
        upload_help = ("Groups allow only 1 file per user, whereas PM allows multiple files for the user.\n\n"
        "If you have a previously uploaded file in a group, the bot will ask if you want to overwrite the file.\n\n\n"
        "Use /start to interact with the bot again :)")

        query.edit_message_text(
            text=upload_help
        )
        return END

    else:
        clear_help = ("Group Chat:\n\nThe 'Clear' button will clear only the file previously uploaded by the user running the command.\n"
        "Other users' files will remain intact.\n\n\n"
        "Private Message:\n\nThe 'Clear' button will open a menu containing files that the user has previously uploaded.\n"
        "Select the file you wish to delete. Use the 'Clear All' button to delete all stored files.\n"
        "Use the 'Done' button when you are done deleting your desired files.\n\n\n"
        "Use /start to interact with the bot again :)")

        query.edit_message_text(
            text=clear_help
        )
        return END

def view(update, context):
    print('view')
    query = update.callback_query
    chat_type = query.message.chat.type
    query.answer()
    # If command called in PM
    if chat_type == 'private':
        userid = query.message.chat_id
        files = db.child('private').child(userid).child('files').get().val()

        # Check if files are empty
        if not files:
            msg = 'There are currently no files stored with me. Please use /start -> Upload to upload a file.'
            query.edit_message_text(text=msg)
            return ConversationHandler.END
        
        # When files are not empty
        res = ""
        for k,v in files.items():
            currentfile = "{} | {}\n".format(k, v['datecreated'])
            res += currentfile
        
        # Display result
        query.edit_message_text(
            text="You currently have these with me:\n{}".format(res)
        )

    # Case for group
    elif chat_type == 'group' or chat_type  == 'supergroup':
        groupid = query.message.chat_id

        files = db.child('group').child(groupid).child('users').get().val()

        # Deal with case where no one has uploads
        if not files:
            msg = 'There are currently no files stored with me. Please use /start -> Upload to upload a file.'
            query.edit_message_text(text=msg)

        # Case with files
        res = ""
        for userid, entry in files.items():
            username = query.message.chat.get_member(userid).user.username
            fullname = query.message.chat.get_member(userid).user.full_name
            date_updated = entry['dateupdated']
            final_entry = "{} ({}) | Updated: {}\n".format(fullname, username, date_updated)
            res += final_entry

        query.edit_message_text(
            text="You currently have these with me:\n{}".format(res)
        )

    # Dealing with channel    
    else:
        msg = 'Channels are currently not supported :('
        query.edit_message_text(
            text=msg
        )
    return ConversationHandler.END

def cancel_upload(update, context):
    print('cancel_upload')
    text = 'Upload cancelled. Use /start to interact with me again :)'
    context.bot.send_message(
        text=text,
        chat_id=update.message.chat_id
    )
    return END

def clear(update, context):
    print('clear')
    query = update.callback_query
    chat_type = query.message.chat.type
    query.answer()
    print(update) 
    print('\n\n')
    if chat_type == 'private':
        user_id = query.from_user.id
        print('user_id: {}'.format(user_id))

        # db.child('private').child(user_id).remove()
        files = db.child('private').child(user_id).child('files').get().val()
        
        # Case where no files exist
        if not files:
            no_file_prompt = 'No data found :( Use /start to interact with the bot again :)'
            query.edit_message_text(
                text=no_file_prompt
            )
            # context.bot.send_message(
            #     text=no_file_prompt,
            #     chat_id=user_id
            # )
            return END

        # Case where files exist
        else:
            button_names = []
            temp = [k for k,v in files.items()]
            for filename in temp:
                filedate = db.child('private').child(user_id).child('files').child(filename).child('datecreated').get().val()
                button_names.append('{} | {}'.format(filename, filedate))

            # Generate keyboard with each filename
            keyboard = generate_clear_keyboard(button_names, 2)

            prompt = "Click filename to delete file. Click 'Clear All' to clear all files. Click 'Done' if you're done."
            query.edit_message_text(
                text=prompt,
                reply_markup=keyboard
            )
            # context.bot.send_message(
            #     text=prompt,
            #     chat_id=user_id,
            #     reply_markup = keyboard
            # )
            return CLEAR_FILES
            
    else:
        group_id = query.message.chat_id
        user_id = query.from_user.id
        print('groupid: {}'.format(group_id))
        print('userid: {}'.format(user_id))

        db.child('group').child(group_id).child('users').child(user_id).remove()

        remove_text = "I have removed your data from my storage. Use /start to interact with me again :)"
        query.edit_message_text(
            text=remove_text
        )
        # context.bot.send_message(
        #     text=remove_text,
        #     chat_id=user_id if chat_type == 'private' else group_id
        # )

        return END

def clear_files(update, context):
    print('clear_files')
    query = update.callback_query
    user_input = query.data.split(" | ")[0]
    userid = query.message.chat_id
    query.answer()
    
    # Case where files still left
    temp_filenamelist = db.child('private').child(userid).child('files').get().val()
    filenamelist = [k for k,v in temp_filenamelist.items()]

    # Check if user wants to clear all
    if user_input == 'Clear All':
        db.child('private').child(userid).child('files').remove()
        text='All files have been cleared. Use /start to interact with me again :)'
        query.edit_message_text(
            text=text
        )

        return END
    
    # For valid user input 
    else:
        # Remove file
        db.child('private').child(userid).child('files').child(user_input).remove()
        
        # Check if no files left
        post_remove_list = db.child('private').child(userid).child('files').get().val()
        if not post_remove_list:
            query.edit_message_text(
                text="All files have been deleted. Use /start to interact with me again :)"
            )

            return END

        button_names = []
        files = db.child('private').child(userid).child('files').get().val()
        temp = [k for k,v in files.items()]
        for filename in temp:
            filedate = db.child('private').child(userid).child('files').child(filename).child('datecreated').get().val()
            button_names.append('{} | {}'.format(filename, filedate))

        # Regenerate keyboard
        keyboard = generate_clear_keyboard(button_names, 2)
        query.edit_message_text(
            text="I have deleted {}.\nClick filename to delete file. Use 'Clear All' to clear all files. Click 'Done' if you're done.".format(user_input),
            reply_markup=keyboard
        )

        return CLEAR_FILES

def clear_files_done(update, context):
    query = update.callback_query

    query.answer()

    query.edit_message_text(
        text='Understood. Use /start to interact with our bot again :)'
    )
    return END

def generate_clear_keyboard(filenamelist, rowsize):
    print('generate_clear_keyboard')
    keyboard = []
    rowcnt = 0
    row = []
    for button in filenamelist:
        row.append(InlineKeyboardButton(text=button, callback_data=button))
        if rowcnt < rowsize:
            rowcnt += 1
        else:
            rowcnt = 0
            keyboard.append(copy.copy(row))
            row = []
    if len(row) != 0:
        keyboard.append(copy.copy(row))
    keyboard.append(
        [
            InlineKeyboardButton(text='Clear All', callback_data='Clear All'),
            InlineKeyboardButton(text='Done', callback_data='Done')
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def find(update, context):
    print('find')
    # Check if query done from group or PM with bot
    query = update.callback_query
    chat_type = query.message.chat.type
    context.chat_data['included'] = []
    context.chat_data['name_id_map'] = {}
    context.chat_data['params'] = {}
    context.chat_data['included_filenames'] = []

    query.answer()

    # Query from group chat
    if chat_type == 'group' or chat_type == 'supergroup':
        group_id = query.message.chat_id

        # Get from db a list of all userIDs for the group
        raw_user_ids = db.child('group').child(group_id).child('users').get().val()

        # Check if user_ids is empty
        if not raw_user_ids:
            prompt_upload = "No data found :( Please use /start -> Upload first."
            query.edit_message_text(
                text=prompt_upload
            )

            return END

        user_ids = list(raw_user_ids.keys())

        # Populate keyboard buttons with names of users
        keyboard = []
        rowcnt = 0
        row = []
        for userid in user_ids:
            username = query.message.chat.get_member(userid).user.username
            fullname = query.message.chat.get_member(userid).user.full_name
            final_name = "{} ({})".format(fullname, username)

            context.chat_data['name_id_map'][final_name] = userid
            row.append(InlineKeyboardButton(text=final_name, callback_data=final_name))
            if rowcnt < 2:
                rowcnt += 1
            else:
                rowcnt = 0
                keyboard.append(copy.copy(row))
                row = []
            
        if len(row) != 0:
            keyboard.append(copy.copy(row))
        keyboard.append([InlineKeyboardButton(text='Done', callback_data='Done'), InlineKeyboardButton(text='Cancel', callback_data='Cancel')])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)

        prompt = "Select who you want to include in the query."
        query.edit_message_text(
            text=prompt,
            reply_markup=keyboard 
        )
        return FIND_PERSONS

    # Query through PM with bot
    elif chat_type == "private":
        userid = query.message.chat_id

        # Check if entry exists in db
        files = db.child('private').child(userid).child('files').get().val()
        if not files:
            text = "No data found :( Please use /start -> Upload first."
            query.edit_message_text(
                text=text
            )
            return END

        # print(files)
        temp_filenames = [k for k,v in files.items()]
        
        for filename in temp_filenames:
            filedate = db.child('private').child(userid).child('files').child(filename).child('datecreated').get().val()
            context.chat_data['included_filenames'].append('{} | {}'.format(filename, filedate))

        # If entry doesn't exist
        if not context.chat_data['included_filenames']:
            prompt_upload = "No data found :( Please use /start -> Upload first."
            
            query.edit_message_text(
                text=prompt_upload
            )
            return END
        
        # Generate keyboard
        keyboard = []
        rowcnt = 0
        row = []
        for user in context.chat_data['included_filenames']:
            row.append(InlineKeyboardButton(text=user, callback_data=user))
            if rowcnt < 2:
                rowcnt += 1
            else:
                rowcnt = 0
                keyboard.append(copy.copy(row))
                row = []
        if len(row) != 0:
            keyboard.append(copy.copy(row))
        keyboard.append([InlineKeyboardButton(text='Cancel', callback_data='Cancel')])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)

        prompt = "Select which files you want to include in the query."
        query.edit_message_text(
            text=prompt,
            reply_markup=keyboard
        )
        return FIND_PERSONS

    # Query through channel
    else:
        query.edit_message_text(
            text="Channels are currently not supported :("
        )
        return END

def generate_keyboard_from_userlist(userlist, rowsize):
    print('generate_keyboard_from_userlist')
    keyboard = []
    rowcnt = 0
    row = []
    for user in userlist:
        row.append(InlineKeyboardButton(text=user, callback_data=user))
        if rowcnt < rowsize:
            rowcnt += 1
        else:
            rowcnt = 0
            keyboard.append(copy.copy(row))
            row = []
    if len(row) != 0:
        keyboard.append(copy.copy(row))
    keyboard.append([InlineKeyboardButton(text='Done', callback_data='Done'), InlineKeyboardButton(text='Cancel', callback_data='Cancel')])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def find_persons_to_query(update, context):
    print("find_persons_to_query")
    query = update.callback_query
    user_selection = query.data
    group_id = query.message.chat.id
    chat_type = query.message.chat.type

    query.answer()

    if chat_type == 'private':
        # User done selecting files
        if user_selection == 'Done':
            prompt_time = "Okay now please give me a start date to search from in the format:\nDD/MM/YYYY HH:MM\nUse '/cancel' to cancel."
            query.edit_message_text(
                text=prompt_time
            )

            return FIND_START

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
                prompt_for_next = "I have included {}. Select other files that you want to include.".format(user_selection)
                query.edit_message_text(
                    text=prompt_for_next,
                    reply_markup=keyboard
                )

                return FIND_PERSONS

            # No users left
            else:
                prompt_for_next = "I see you've added all your files already.\nPlease give me a start date to search from in the format:\nDD/MM/YYYY HH:MM"
                query.edit_message_text(
                    text=prompt_for_next
                )

                return FIND_START

    else:
        # User done selecting users
        if user_selection == 'Done':
            prompt_time = "Okay, now please give me a start date to search from in the format:\nDD/MM/YYYY HH:MM"
            query.edit_message_text(
                    text=prompt_time
            )

            return FIND_START

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
                prompt_for_next = "I have included {}. Select other files that you want to include.".format(user_selection)
                query.edit_message_text(
                    text=prompt_for_next,
                    reply_markup=keyboard
                )
                
                return FIND_PERSONS

            # No users left
            else:
                prompt_for_next = "I see you've added all your friends already.\nPlease give me a start date to search from in the format:\nDD/MM/YYYY HH:MM"
                query.edit_message_text(
                    text=prompt_for_next
                )

                return FIND_START

def cancel_find_callback(update, context):
    print('cancel_find_callback')
    query = update.callback_query
    cancel_text = "We have cancelled your request.\nUse /start to interact with the bot again :)"
    query.answer()
    query.edit_message_text(
        text=cancel_text
    )
    return END

def cancel_find(update, context):
    print('cancel_find')
    cancel_text = "We have cancelled your request.\nUse /start to interact with the bot again :)"
    context.bot.send_message(
        text=cancel_text,
        chat_id=update.message.chat_id
    )
    return END

def find_start_time(update, context):
    print('find_start_time')
    user_input = update.message.text
    try:
        parsed_date = datetime.strptime(user_input, "%d/%m/%Y %H:%M")
        context.chat_data['params']['start'] = parsed_date
        prompt_end_time = "You have provided a start time.\nPlease give me an end date to search from in the format:\nDD/MM/YYYY HH:MM\nTo cancel, type '/cancel'."
        context.bot.send_message(
            text=prompt_end_time,
            chat_id=update.message.chat_id
        )
        return FIND_END

    except ValueError:
        error_prompt = "I do not understand {}.\nPlease give me a start date to search from in the format:\nDD/MM/YYYY HH:MM\nTo cancel, type '/cancel'".format(user_input)
        context.bot.send_message(
            text=error_prompt,
            chat_id=update.message.chat_id
        )
        return FIND_START

def find_end_time(update, context):
    print('find_end_time')
    user_input = update.message.text
    try:
        parsed_date = datetime.strptime(user_input, "%d/%m/%Y %H:%M")
        context.chat_data['params']['end'] = parsed_date
        prompt_end_time = "You have provided an end time.\nPlease give me a minimum required interval (between 0 to 24).\nTo cancel, type '/cancel'."
        context.bot.send_message(
            text=prompt_end_time,
            chat_id=update.message.chat_id
        )
        return FIND_INT

    except ValueError:
        error_prompt = "I do not understand {}.\nPlease give me an end date to search from in the format:\nDD/MM/YYYY HH:MM\nTo cancel, type '/cancel'".format(user_input)
        context.bot.send_message(
            text=error_prompt,
            chat_id=update.message.chat_id
        )
        return FIND_END

def process_result(res_dict):
    print('process_result')
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
    print('find_min_interval')
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
        return END
    except ValueError:
        error_prompt = "I do not understand {}.\nPlease give me a minimum required interval (between 0 to 24).\nTo cancel, type '/cancel'.".format(user_input)
        context.bot.send_message(
            text=error_prompt,
            chat_id=update.message.chat_id
        )
        return FIND_INT

def upload(update, context):
    print('upload')
    query = update.callback_query
    group_id = query.message.chat_id
    user_id = query.from_user.id
    chat_type = query.message.chat.type

    query.answer()

    if chat_type == "channel":
        prompt = "I currently do not support channels :("
        query.edit_message_text(
            text=prompt
        )
        # context.bot.send_message(
        #     text=prompt,
        #     chat_id=group_id
        # )
        return END

    is_PM = False if chat_type == "group" or chat_type == "supergroup" else True

    # Case for PM
    if is_PM:
        upload_text = "Please upload your .ics files or use '/cancel' to cancel."
        query.edit_message_text(
            text=upload_text
        )
        # context.bot.send_message(
        #     text=upload_text,
        #     chat_id=update.message.chat_id
        # )
        return ON_DOC_UPLOAD

    # Case for group chat
    else:
        # Check if ics file for this user already exists in db
        if db.child('group').child(group_id).child('users').child(user_id).child('icalrep').get().val() != None:
            # print('Prompt group overwrite')
            date = db.child('group').child(group_id).child('users').child(user_id).child('dateupdated').get().val()
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text='Yes', callback_data='Yes'), 
                        InlineKeyboardButton(text='No', callback_data='No')
                    ]
                ]
            )
            prompt = "You already have an .ics with me already uploaded on {}.\nUse 'Yes' to overwrite or 'No' to cancel".format(date)
            query.edit_message_text(
                text=prompt,
                reply_markup=keyboard
            )

            return ASK_CONFIRMATION

        upload_text = "Please upload your .ics files or use '/cancel' to cancel."
        query.edit_message_text(
            text=upload_text
        )

        return ON_DOC_UPLOAD

def reprompt(update, context):
    print('reprompt')
    reprompt_text = 'Invalid file uploaded! Please try again.'
    context.bot.send_message(
        text=reprompt_text,
        chat_id=update.message.chat_id
    )
    return ON_DOC_UPLOAD

def ask_confirmation(update, context):
    print('ask_confirmation')
    query = update.callback_query
    user_selection = query.data
    if user_selection == 'Yes':
        upload_text = "Please upload your .ics files or use '/cancel' to cancel."
        query.edit_message_text(
            text=upload_text
        )

        return ON_DOC_UPLOAD
    else:
        query.edit_message_text(
            text='Understood. Use /start to interact with me again :)'
        )

        return END

def on_doc_upload(update, context):   
    print('on_doc_upload') 
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

    confirmation_grp = "{}'s file has been successfully uploaded.\nUse /start to interact with me again :)".format(update.message.from_user.username)
    confirmation_prv = "{} has been successfully uploaded.\nUse /start to interact with me again :)".format(filename)
    context.bot.send_message(
        text=confirmation_prv if is_PM else confirmation_grp,
        chat_id=group_id
    )

    return END

def error(update, context):
    print(context.error)
    context.bot.send_message(
        text="ERROR! Bot-chan itai! Plz don't do that kudasai ><",
        chat_id = update.message.chat_id
    )

def aslocaltimestr(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None).strftime('%Y/%m/%d %H:%M')

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher;

    # Upload convo handler
    upload_convo_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(upload, pattern='^' + str(UPLOAD) + '$')],
        states={
            ON_DOC_UPLOAD : [
                MessageHandler(Filters.document.file_extension("ics"), on_doc_upload), 
                CommandHandler('cancel', cancel_upload), 
                MessageHandler(~Filters.document.file_extension("ics"), reprompt)
            ],
            ASK_CONFIRMATION : [CallbackQueryHandler(ask_confirmation)]
        },
        fallbacks=[],
        map_to_parent={
            END : END
        }
    )

    # Clear convo handler
    clear_convo_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(clear, pattern='^' + str(CLEAR) + '$')],
        states={
            CLEAR_FILES : [CallbackQueryHandler(clear_files_done, pattern='^Done$'), CallbackQueryHandler(clear_files)]
        },
        fallbacks=[],
        map_to_parent={
            END : END
        }
    )

    # Find convo handler
    find_convo_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(find, pattern='^' + str(FIND) + '$')],
        states={
            FIND_PERSONS : [CallbackQueryHandler(cancel_find_callback, pattern="^Cancel$"), CallbackQueryHandler(find_persons_to_query)],
            FIND_START : [CommandHandler('cancel', cancel_find), MessageHandler(Filters.text, find_start_time)],
            FIND_END : [CommandHandler("cancel", cancel_find), MessageHandler(Filters.text, find_end_time)],
            FIND_INT : [CommandHandler("cancel", cancel_find), MessageHandler(Filters.text, find_min_interval)]
        },
        fallbacks=[],
        map_to_parent={
            END : END
        }
    )

    # Help convo handler
    help_convo_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(help, pattern='^' + str(HELP) + '$')],
        states={
            FAQ_SELECTION : [CallbackQueryHandler(faq_selection)],
            FAQ_PURPOSE_SELECTOR : [CallbackQueryHandler(faq_purpose_selector)],
            FAQ_COMMAND_SELECTOR : [CallbackQueryHandler(faq_command_selector)]
        },
        fallbacks=[],
        map_to_parent={
            END : END
        }
    )

    # Selection function
    select_handlers = [
            help_convo_handler,
            CallbackQueryHandler(view, pattern='^' + str(VIEW) + '$'),
            CallbackQueryHandler(end, pattern='^' + str(END) + '$'),
            find_convo_handler,
            clear_convo_handler,
            upload_convo_handler
        ]

    # Add main conversation handler for user interaction
    interact_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTION : select_handlers,
            END : [CommandHandler('start', start)]
        },
        fallbacks=[]
    )
    dp.add_handler(interact_conv_handler)

    # Add error handler for bot
    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()