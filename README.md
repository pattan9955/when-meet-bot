# when-meet-bot
A Telegram bot that accepts and stores multiple e-calendar files (.ics format) and finds common free times when queried.

proofOfConcept.py is a Python script that describes an algorithm which accepts as input a list of filepaths to iCalendar files (.ics) as well as a start date, end date and a minimum duration. It then finds blocks of free time common amongst all .ics files that are at least of the given minimum duration, between the provided start and end dates.

A skeleton for the Telegram bot has been prepared with a connection to the Firebase Realtime Database that will be used to store the provided .ics files. Additional features will be made for the Telegram bot in future.

Known Issues:
1) Parsing currently ignores timezone information. May consider standardizing all timings to UTC or GMT +8 (Singapore) time.

Todo:
1) Implement find function for the Telegram bot.
2) Implement help function for the Telegram bot.
3) Implement uploading of .ics files for the Telegram bot.
