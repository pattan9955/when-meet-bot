import icalendar
from datetime import datetime, timedelta, date
import copy
from intervaltree import Interval, IntervalTree
import recurring_ical_events
from testfiles import *

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
    
    # Unfolds all events (Including recurring events) between start and end datetime
    events = recurring_ical_events.of(fcal).between(start_datetime, end_datetime)
    
    event_list = []
    for event in events:
        temp_start = event['DTSTART'].dt
        temp_end = event['DTEND'].dt

        if isinstance(temp_start, date):
            temp_start = datetime(temp_start.year, temp_start.month, temp_start.day)
        if isinstance(temp_end, date):
            temp_end = datetime(temp_end.year, temp_end.month, temp_end.day)
            temp_end += timedelta(1)

        if temp_start < start_datetime:
            temp_start = start_datetime
        if temp_end > end_datetime:
            temp_end = end_datetime

        event_list.append([temp_start, temp_end])
    # print(sorted(event_list, key = lambda e : e[0]))
    return sorted(event_list, key = lambda e : e[0])

# def parse_output_ics(in_filepath):
    '''
    Takes as input a filepath to a .ics file and returns a list of events in the ics file,
    represented as lists of [start_datetime, end_datetime], sorted in ascending order
    by start_datetime.

    Future Changes: 
    1) Currently does not work on recurring events
    2) Currently does not deal with events where end_datetime does not exist
    3) Change input to function to take in a string representation of an .ics file in line with 
        future changes to merge_ics
    4) Currently does not work on different timezones. (Consider using regex matching)

    :param in_filepath: A string representing a filepath to the .ics file to be parsed.
    :returns: A list of events, represented as a list of lists of [start_datetime, end_datetime], sorted in ascending order
            by start_datetime.
    '''
    events_list = []
    with open(in_filepath) as f:
        # Temp container for start date
        start_date_temp = None
        
        for line in f:
            # When start datetime found
            if line[0:7] == "DTSTART":
                start_date = line.split(":")[1].strip()
                
                # Deal with UTC dates
                if start_date[-1] == "Z":
                    start_date = start_date[:-1]
                
                # Parse date
                start_date_temp = datetime.strptime(start_date, "%Y%m%dT%H%M%S")

            # When end datetime found
            elif line[0:5] == "DTEND":
                end_date = line.split(":")[1].strip()

                # Deal with UTC dates
                if end_date[-1] == "Z":
                    end_date = end_date[:-1]

                # Parse date
                end_date = datetime.strptime(end_date, "%Y%m%dT%H%M%S")

                # Append event to events_list
                event = [copy.copy(start_date_temp), end_date]
                events_list.append(event)

                # Resets start_date_temp
                start_date_temp = None
    
    return sorted(events_list, key = lambda e : e[0])
 
# def filter(events_list, start_date, end_date):
    '''
    Takes in a list of events represented as a list of lists of [start_datetime, end_datetime] and
    filters out events that do not overlap with the interval [start_date, end_date] as prescribed
    by the user. Operation performed using an interval tree.

    Future Changes:
    1) Currently does not handle overnight events properly in filtering, since events that spill over to 
    the next day retain their original end date -> Causes KeyError in main function. Need to manually edit the 
    start/end date during filtering so as to respect the provided start/end date by the user.

    :param events_list: A list of events represented as a list of lists of [start_datetime, end_datetime]
    :param start_date: A datetime object representing the start date of the desired search space.
    :param end_date: A datetime object representing the end date of the desired search space.
    :returns: A filtered list of events that overlap with the given [start_date, end_date] interval.
    '''
    interval_list = []
    for event in events_list:
        event_interval = Interval(event[0], event[1])
        interval_list.append(event_interval)

    tree = IntervalTree(interval_list)

    filtered_raw = list(tree.overlap(start_date, end_date))
    
    filtered = []
    for item in filtered_raw:
        temp = [item.begin, item.end]
        filtered.append(temp)
    
    # print(filtered)
    return filtered

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
    
    # Check for case where end_datetime less than start_datetime
    try:
        if end_datetime <= start_datetime:
            raise ValueError
    except ValueError:
        print("Invalid interval provided!")
        
    start_date = start_datetime.date()
    end_date = end_datetime.date()

    free_time_dict = {}
    for date in daterange(start_date, end_date + timedelta(days=1)):
        free_time_dict[date] = [True for i in range(24)]

    for event in events:
        event_start_date = event[0].date()
        event_end_date = event[1].date()
        event_start_time = event[0].time().hour
        cond = event[1].time().minute > 0 or event[1].time().second > 0 or event[1].time().microsecond > 0
        event_end_time = (event[1].time().hour + 1) if (cond) else event[1].time().hour

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
            for i in range(0, event_end_time + 1):
                temp[i] = False

    # print(free_time_dict)
    final_results = {}

    # Find intervals of min size provided
    for date, timetable in free_time_dict.items():
        results = []
        current_start = -1
        current_end = -1
        interval_cnt = 0
        for i in range(23):
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
        if interval_cnt > 0 and current_end == -1:
            results.append((current_start, 24))

        final_results[str(date)] = results

    return final_results
    # print(final_results)    

if __name__ == '__main__':
    start = datetime(2021, 6, 18, 0, 0, 0)
    end = datetime(2021, 8, 18, 0, 0, 0)
    # print(new_parse_output_ics(fel_str, start, end))
    # print(find_free_time([fel_str], start, end, 5))
    print(find_free_time([GAV_STR, FEL_STR], start, end, 22))