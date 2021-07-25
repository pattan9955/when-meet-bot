import icalendar
import calendar
from datetime import datetime, timedelta, date
import recurring_ical_events
import pytz
# from testfiles import *

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
            # print("temp_start: {}".format(temp_start))

        if isinstance(temp_end, date) and not isinstance(temp_end, datetime):
            temp_end = datetime(temp_end.year, temp_end.month, temp_end.day)
            # print("temp_end: {}".format(temp_end))
            # temp_end += timedelta(1)

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

    # Define timezone object for SG timing
    sgt = pytz.timezone('Asia/Singapore')
    start_datetime = sgt.localize(start_datetime)
    end_datetime = sgt.localize(end_datetime)
        
    end_date = end_datetime.date()
    end_hour = end_datetime.time().hour

    # Extract time information from search params
    start_hour = start_datetime.time().hour
    start_date = start_datetime.date()
    start_round_cond = start_datetime.time().minute > 0 or start_datetime.time().second > 0 or start_datetime.time().microsecond > 0
    if start_round_cond:
        start_hour = (start_datetime + timedelta(hours=1)).time().hour
        start_date = (start_datetime + timedelta(hours=1)).date()

    # Populate start date only with start time considerations
    free_time_dict = {}
    free_time_dict[start_date] = []
    for i in range(24):
        if i < start_hour:
            free_time_dict[start_date].append(False)
        else:
            free_time_dict[start_date].append(True)
    
    # Populate in between dates i.e. exclusive of start and end dates
    for date in daterange(start_date + timedelta(days=1), end_date):
        free_time_dict[date] = [True for i in range(24)]

    # Populate end date only with end time considerations
    free_time_dict[end_date] = []
    for i in range(24):
        if i >= end_hour:
            free_time_dict[end_date].append(False)
        else:
            free_time_dict[end_date].append(True)

    for event in events:
        event_start_date = event[0].date()
        event_start_time = event[0].time().hour
        
        cond = event[1].time().minute > 0 or event[1].time().second > 0 or event[1].time().microsecond > 0

        # Round off event end time
        if cond:
            event[1] = event[1] + timedelta(hours=1)
        
            if event[1] > end_datetime:
                event[1] = end_datetime

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
    # print("\n")
    final_results = {}

    # Find intervals of min size provided
    spill_tank = []
    spills_over = False
    spill_interval = 0

    for date, timetable in free_time_dict.items():
        results = []
        current_start = -1
        current_end = -1
        interval_cnt = 0

        for i in range(24):
            if not spills_over:
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
                if timetable[i]:
                    if interval_cnt == 0:
                        current_start = i
                    interval_cnt += 1
                else:
                    if (interval_cnt + spill_interval >= min_hourly_interval):
                        current_end = i

                        for spill in spill_tank:
                            spill_date = spill[0]
                            spill_time = spill[1]
                            final_results[spill_date].append(spill_time)

                        if interval_cnt > 0:
                            results.append((current_start, current_end))

                    spill_tank = []
                    spills_over = False
                    spill_interval = 0
                    current_start = -1
                    current_end = -1
                    interval_cnt = 0
        
        if interval_cnt > 0 and current_end == -1:
            if not spills_over:
                formatted_date = date.strftime("%d-%m-%Y") + " (" + calendar.day_name[date.weekday()] + ")"   
                spill_tank.append([formatted_date,(current_start, 24)])
                spills_over = True
                spill_interval = interval_cnt

            else:
                spill_interval += interval_cnt
                formatted_date = date.strftime("%d-%m-%Y") + " (" + calendar.day_name[date.weekday()] + ")"   
                spill_tank.append([formatted_date,(current_start, 24)])

        formatted_date = date.strftime("%d-%m-%Y") + " (" + calendar.day_name[date.weekday()] + ")" 
        final_results[formatted_date] = results

    if spill_tank:
        for spill in spill_tank:
            spill_date = spill[0]
            spill_time = spill[1]
            final_results[spill_date].append(spill_time)

    # print(final_results)
    # print('\n')
    return result_formatter(final_results)
    # print(final_results)    

def format_start_end(time):
    # start = time[0] % 24
    # end = time[1] % 24

    start = time[0]
    end = time[1]
    
    # Format start time
    if start < 10:
        start = '0{}00'.format(start)
    else:
        start = '{}00'.format(start)

    # Format end time
    if end < 10:
        end = '0{}00'.format(end)
    else:
        end = '{}00'.format(end)

    interval = "    {}hrs to {}hrs".format(start, end)

    return interval

def result_formatter(raw):
    # print('raw: {}'.format(raw))
    if not raw:
        return {}

    result = {}
    prev_time = None
    prev_date = None
    current_date = None
    current_time = None

    # Pre-populate result dict with empty lists, 
    # strip out days with no results
    for date,times in raw.items():
        if times:
            result[date] = []

    for date,times in raw.items():
        # If no free times for that day
        if not times:
            # Check if interval of spillover is within provided min interval
            if prev_time and prev_date:
                if current_date and current_time:
                    temp = format_start_end((prev_time[0], current_time[1]))
                    temp += ", {}".format(current_date)
                    result[prev_date].append(temp)
                    current_date, current_time = None, None 
                else:
                    result[prev_date].append(format_start_end(prev_time))
                prev_time, prev_date = None, None
            continue
        
        for time in times:
            
            # Catch cases where end time is at 2400hrs
            # Sub cases caught: 
            # 1) if whole day free i.e. (0,24)
            # 2) partial day free i.e. (5,24) -> may spill over to next day, may also end current spill over
            #   at prev date/time if any
            if time[1] == 24:
                if prev_date and prev_time:
                    if time[0] == 0:
                        current_date = date
                        current_time = time
                    else:
                        if current_date and current_time:
                            temp = format_start_end((prev_time[0], current_time[1]))
                            temp += ", {}".format(current_date)
                            result[prev_date].append(temp)
                            current_date, current_time = None, None 
                        else:
                            result[prev_date].append(format_start_end(prev_time))
                        prev_time = time
                        prev_date = date
                    break
                prev_time = time
                prev_date = date
            
            # Catch cases where start time is 0000hrs but does not end at 2400hrs
            # i.e. is a valid interval on its own or ends a spillover
            elif time[0] == 0:
                if prev_time and prev_date:
                    temp = format_start_end((prev_time[0],time[1]))
                    temp += ", {}".format(date)
                    result[prev_date].append(temp)
                    prev_time, prev_date, current_time, current_date = None, None, None, None
                    
                else:
                    result[date].append(format_start_end(time))

            # Catches any other valid interval i.e. does not start at 0000hrs or end at 2400hrs
            else:
                # Handles any previous spillovers
                if prev_time and prev_date:
                    if current_date and current_time:
                        temp = format_start_end((prev_time[0], current_time[1]))
                        temp += ", {}".format(current_date)
                        result[prev_date].append(temp)
                        prev_date, prev_time, current_date, current_time = None, None, None, None

                    # Catches cases where previous supposed spillover was just a valid interval by itself
                    else:
                        result[prev_date].append(format_start_end(prev_time))
                        prev_date = None
                        prev_time = None
                
                # Add current interval
                result[date].append(format_start_end(time))

    # Accounts for remaining supposed spillovers at the end
    if prev_date and prev_time:
        if current_date and current_time:
            if current_time[0] == 0:
                temp = format_start_end((prev_time[0], current_time[1]))
                temp += ", {}".format(current_date)
                result[prev_date].append(temp)
            else:
                result[prev_date].append(format_start_end(prev_time))
                result[current_date].append(format_start_end(current_time))

        else:
            result[prev_date].append(format_start_end(prev_time))

    final = {}
    # Clean up empty dates
    for date, times in result.items():
        if times:
            final[date] = times

    return final

if __name__ == '__main__':
    
    '''
    find_free_time test cases
    '''
    # start = datetime(2021, 5, 12, 0, 0, 0)
    # end = datetime(2021, 5, 16, 0, 0, 0)
    # print(str(find_free_time([PAT_NUS_STR, NAY_NUS_STR, FEL_NEW_STR], start, end, 14)))
    # print(str(find_free_time([PAT_NUS_STR, NAY_NUS_STR, FEL_NEW_STR], start, end, 1)))
    # print(str(find_free_time([PAT_NUS_STR, NAY_NUS_STR, FEL_NEW_STR], start, end, 51)))
    # print(str(find_free_time([PAT_NUS_STR, NAY_NUS_STR, FEL_NEW_STR], start, end, 52)))
    # print(str(find_free_time([PAT_NUS_STR, NAY_NUS_STR, FEL_NEW_STR], start, end, 20)))

    # start = datetime(2021, 5, 10, 0, 0, 0)
    # end = datetime(2021, 5, 20, 0, 0, 0)
    # print(str(find_free_time([PAT_NUS_STR, NAY_NUS_STR, FEL_NEW_STR], start, end, 14)))
    # print(str(find_free_time([PAT_NUS_STR, NAY_NUS_STR, FEL_NEW_STR], start, end, 48)))
    # print(str(find_free_time([PAT_NUS_STR, NAY_NUS_STR, FEL_NEW_STR], start, end, 72)))
    # print(str(find_free_time([PAT_NUS_STR, NAY_NUS_STR, FEL_NEW_STR], start, end, 1)))
    # print(str(find_free_time([PAT_NUS_STR, NAY_NUS_STR, FEL_NEW_STR], start, end, 24)))

    # start = datetime(2021, 5, 10, 0, 0, 0)
    # end = datetime(2021, 5, 20, 0, 0, 0)
    # print(str(find_free_time([JIAZ_STR, NAY_NUS_STR, FEL_NEW_STR, GAV_STR], start, end, 14)))
    # print(str(find_free_time([JIAZ_STR, NAY_NUS_STR, FEL_NEW_STR, GAV_STR], start, end, 48)))
    # print(str(find_free_time([JIAZ_STR, NAY_NUS_STR, FEL_NEW_STR, GAV_STR], start, end, 72)))
    # print(str(find_free_time([JIAZ_STR, NAY_NUS_STR, FEL_NEW_STR, GAV_STR], start, end, 1)))
    # print(str(find_free_time([JIAZ_STR, NAY_NUS_STR, FEL_NEW_STR, GAV_STR], start, end, 24)))

    # start = datetime(2021, 5, 28, 0, 0, 0)
    # end = datetime(2021, 6, 1, 0, 0, 0)
    # print(str(find_free_time([NAY_NUS_STR, FEL_NEW_STR, PAT_NUS_STR], start, end, 1)))

    # start = datetime(2021, 6, 27, 0, 0, 0)
    # end = datetime(2021, 6, 30, 0, 0, 0)
    # print(str(find_free_time([NAY_NUS_STR, FEL_NEW_STR, PAT_NUS_STR], start, end, 1)))


    '''
    result_formatter test cases
    '''
    test1 = {
        '1' : [(2,3), (17,24)],
        '2' : [(4,24)]
    } 
    # {'1': ['    0200hrs - 0300hrs', '    1700hrs - 2400hrs'], '2': ['    0400hrs - 2400hrs']}

    test2 = {
        '1' : [(2,3), (5,24)],
        '2' : [(0,24)],
        '3' : [(0,24)],
        '4' : [(5,24)]
    }
    # {'1': ['    0200hrs - 0300hrs', '    0500hrs - 2400hrs (3)'], '4': ['    0500hrs - 2400hrs']}

    test3 = {
        '1' : [(0,12)],
        '2' : [(0,24)],
        '3' : [(0,4), (11,24)]
    }
    # {'1': ['    0000hrs - 1200hrs'], '2': ['    0000hrs - 0400hrs (3)'], '3': ['    1100hrs - 2400hrs']}

    test4 = {
        '1' : [(0,24)],
        '2' : [(0,24)],
        '3' : [],
        '4' : [(1,4), (5,8)]
    }
    # {'1': ['    0000hrs - 2400hrs (2)'], '4': ['    0100hrs - 0400hrs', '    0500hrs - 0800hrs']}

    test5 = {
        '1' : [(0,24)],
        '2' : [],
        '3' : [],
        '4' : [(1,4), (5,8)]
    }
    # {'1': ['    0000hrs - 2400hrs'], '4': ['    0100hrs - 0400hrs', '    0500hrs - 0800hrs']}

    test6 = {
        '1' : [(0,24)],
        '2' : [],
        '3' : [(5,24)],
        '4' : [],
        '5' : [(1,4), (5,8)]
    }
    # {'1': ['    0000hrs - 2400hrs'], '3': ['    0500hrs - 2400hrs'], '5': ['    0100hrs - 0400hrs', '    0500hrs - 0800hrs']}

    test7 = {
        '1' : [(0,24)],
        '2' : [],
        '3' : [(5,24)],
        '4' : [(0,1)],
        '5' : [(1,4), (5,8)]
    }
    # {'1': ['    0000hrs - 2400hrs'], '3': ['    0500hrs - 0100hrs (4)'], '5': ['    0100hrs - 0400hrs', '    0500hrs - 0800hrs']}

    test8 = {
        '1' : [(5,24)],
        '2' : [(0,3), (19,24)],
        '3' : [],
        '4' : [(0,24)],
        '5' : [(0,24)]
    }
    # {'1': ['    0500hrs - 0300hrs (2)'], '2': ['    1900hrs - 2400hrs'], '4': ['    0000hrs - 2400hrs (5)']}

    test9 = {
        '1' : [(0,24)],
        '2' : [(0,24)],
        '3' : [],
        '4' : []
    }
    # {'1': ['    0000hrs - 2400hrs (2)']}

    test10 = {
        '1' : [(0, 24)],
        '2' : [(0, 24)], 
        '3' : [(0, 14), (17, 24)]
    }
    # {'1': ['    0000hrs - 1400hrs (3)'], '3': ['    1700hrs - 2400hrs']}

    # print(result_formatter(test1))