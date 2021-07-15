import icalendar
from datetime import datetime, timedelta, date
import copy
# from intervaltree import Interval, IntervalTree
import recurring_ical_events
import pytz
# from testfiles import *

# class Event():
    # '''
    # Constructor for an event. Event should contain a starting datetime, an ending datetime and a string representation
    # of the event as defined in the .ics file.

    # Events are ordered by their start_datetime
    # '''
    # def __init__(self, start_datetime, end_datetime, string_rep, is_recurring, EXDATE_ls, recur_rules) -> None:
    #     self.start_datetime  = start_datetime
    #     self.end_datetime = end_datetime
    #     self.string_rep = string_rep

    # def __repr__(self) -> str:
    #     return repr((self.start_datetime, self.end_datetime, self.string_rep))

    # def __eq__(self, other) -> bool:
    #     self.start_datetime == other.start_datetime

def merge_ics(incoming_ics):
    '''
    Take as input a list of strings containing the contents of .ics files and merges the events
    in each .ics file into a string representing the contents of a new .ics file.

    :param incoming_ics: A list of strings containing contents of .ics files
    :returns: A string containing the contents of the merged .ics files
    '''

    calxs = "BEGIN:VCALENDAR\n"
    for file in incoming_ics:
            intermediate = ""
            take = False
            temp = file.split('\n')

            for line in temp:
                if line == "END:VEVENT":
                    take = False
                    temp = line + '\n'
                    intermediate += temp
                elif line == "BEGIN:VEVENT":
                    take = True
                    temp = line + '\n'
                    intermediate += temp
                else:
                    if take:
                        temp = line + '\n'
                        intermediate += temp
            calxs += intermediate
    calxs += "END:VCALENDAR"

    return calxs

def new_parse_output_ics(cal_str, start_datetime, end_datetime):
    '''
    Takes as input a string representing the contents of an .ics file and a start/end datetime, 
    and returns a list of events in the .ics file that fall between the provided start/end datetimes, 
    represented as lists of [start_datetime, end_datetime], sorted in ascending order by 
    start_datetime. Function unfolds recurring events, preserves provided timezone 
    information and deals with EXDATEs for recurring events.

    Future Changes:
    1) Currently does not do anything with provided timezone information. May
        consider standardizing to UTC or GMT+8 (SG) time, or allowing user to 
        specify a specific timezone.

    :param cal_str: A string representing the contents of an .ics file
    :param start_datetime: A tuple representing a datetime object or a datetime object
        indicating the start datetime of the desired search space.
    :param end_datetime: A tuple representing a datetime object or a datetime object
        indicating the end datetime of the desired search space.
    :returns: A filtered list of events that overlap with the given 
        [start_datetime, end_datetime] sorted in ascending order by start_datetime.
    '''
    
    fcal = icalendar.Calendar.from_ical(cal_str)
    
    # Define timezone object for SG timing
    sgt = pytz.timezone('Asia/Singapore')
   
    # Unfolds all events (Including recurring events) between start and end datetime
    events = recurring_ical_events.of(fcal).between(start_datetime, end_datetime)
    
    start_datetime = sgt.localize(start_datetime)
    end_datetime = sgt.localize(end_datetime)    

    event_list = []
    for event in events:
        temp_start = event['DTSTART'].dt
        temp_end = event['DTEND'].dt

        if isinstance(temp_start, date) and not isinstance(temp_start, datetime):
            temp_start = datetime(temp_start.year, temp_start.month, temp_start.day)
        if isinstance(temp_end, date) and not isinstance(temp_end, datetime):
            temp_end = datetime(temp_end.year, temp_end.month, temp_end.day)
            temp_end += timedelta(1)

        # Convert event start and end times to SG timing
        temp_start = temp_start.astimezone(sgt)
        temp_end = temp_end.astimezone(sgt)

        if temp_start < start_datetime:
            temp_start = start_datetime
        if temp_end > end_datetime:
            temp_end = end_datetime

        event_list.append([temp_start, temp_end])
    # print(sorted(event_list, key = lambda e : e[0]))
    return sorted(event_list, key = lambda e : e[0])

def daterange(start_date, end_date):
    '''
    A function that allows for iteration of all dates between the provided start and end date.

    :param start_date: A datetime object representing the start date of the iteration.
    :param end_date: A datetime object representing the end date of the iteration.
    :returns: A generator that allows for iteration of all dates between the provided start and end dates.
    '''
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)

def find_free_time(input_ics_strs, start_datetime, end_datetime, min_hourly_interval):
    '''
    A function that takes in a list of filepaths to .ics files and prints common blocks of free time that are
    at least as long as the given minimum duration between the given start and end date.

    Future Changes:
    1) Change the printing format of the results.
        i) Time intervals to be formatted as datetime objects.
        ii) To be optimized for viewing in a Telegram bot/app environment.
    2) Results may need to be returned from the function for further processing by other functions.

    :param in_filepath: A list of strings indicating filepaths to .ics files.
    :param start_datetime: A datetime object representing the start date of the desired search interval.
    :param end_datetime: A datetime object representing the end date of the desired search interval.
    :param min_hourly_interval: A number representing the minimum duration a block of free time needs to be
            in order to be considered a valid block of free time.
    '''
    events = new_parse_output_ics(merge_ics(input_ics_strs) , start_datetime, end_datetime)
    # print(events)
    # Check for case where end_datetime less than start_datetime
    if end_datetime <= start_datetime:
        raise ValueError
        
    start_date = start_datetime.date()
    end_date = end_datetime.date()

    free_time_dict = {}
    for date in daterange(start_date, end_date + timedelta(days=1)):
        free_time_dict[date] = [True for i in range(24)]

    for event in events:
        event_start_date = event[0].date()
        event_start_time = event[0].time().hour
        
        cond = event[1].time().minute > 0 or event[1].time().second > 0 or event[1].time().microsecond > 0

        # Round off event end time
        if cond:
            event[1] = event[1] + timedelta(hours=1)
        
        event_end_time = event[1].time().hour
        event_end_date = event[1].date()

        # Case 1: Start and end date are the same
        if (event_start_date == event_end_date):
            temp = free_time_dict[event_start_date]
            for i in range(event_start_time, event_end_time):
                temp[i] = False
        
        # Case 2: Start and end date are different
        else:
            # Label all dates between start exclusive and end exclusive to be false
            for date in daterange(event_start_date + timedelta(days=1), event_end_date):
                free_time_dict[date] = [False for i in range(24)]
            
            # Look only at start and end dates and label accordingly
            temp = free_time_dict[event_start_date]
            for i in range(event_start_time, 24):
                temp[i] = False

            temp = free_time_dict[event_end_date]
            for i in range(0, event_end_time):
                temp[i] = False

    # for k,v in free_time_dict.items():
    #     print('{}:{}'.format(k,v))
    # print(free_time_dict)
    final_results = {}

    # Find intervals of min size provided
    temp = None
    spills_over = False
    spill_interval = 0
    spill_date = None

    for date, timetable in free_time_dict.items():
        results = []
        current_start = -1
        current_end = -1
        interval_cnt = 0
        if not spills_over:
            for i in range(24):
                if timetable[i]:
                    if interval_cnt == 0:
                        current_start = i
                    interval_cnt += 1
                else:
                    if (interval_cnt >= min_hourly_interval):
                        current_end = i
                        results.append((current_start, current_end))
                    current_start = -1
                    current_end = -1
                    interval_cnt = 0
        else:
            for i in range(24):
                if timetable[i]:
                    if interval_cnt == 0:
                        current_start = i
                    interval_cnt += 1
                else:
                    if (interval_cnt + spill_interval >= min_hourly_interval):
                        current_end = i
                        final_results[spill_date].append(temp)
                        results.append((current_start, current_end))
                    temp = None
                    spills_over = False
                    spill_interval = 0
                    current_start = -1
                    current_end = -1
                    interval_cnt = 0
        
        if interval_cnt > 0 and current_end == -1:
            temp = (current_start, 24)
            spills_over = True
            spill_interval = interval_cnt
            spill_date = str(date)

        final_results[str(date)] = results

    return final_results
    # print(final_results)    

if __name__ == '__main__':
    start = datetime(2021, 3, 15, 0, 0, 0)
    end = datetime(2021, 3, 21, 23, 0, 0)
    # print(new_parse_output_ics(fel_str, start, end))
    # print(find_free_time([fel_str], start, end, 5))
    # print('\n' + str(find_free_time([MALC_STR, FEL_STR], start, end, 14)))