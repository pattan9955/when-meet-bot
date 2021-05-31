# import icalendar
from datetime import datetime, timedelta
import copy
from intervaltree import Interval, IntervalTree

# class Event():
#     '''
#     Constructor for an event. Event should contain a starting datetime, an ending datetime and a string representation
#     of the event as defined in the .ics file.

#     Events are ordered by their start_datetime
#     '''
#     def __init__(self, start_datetime, end_datetime, string_rep, is_recurring, EXDATE_ls, recur_rules) -> None:
#         self.start_datetime  = start_datetime
#         self.end_datetime = end_datetime
#         self.string_rep = string_rep

#     def __repr__(self) -> str:
#         return repr((self.start_datetime, self.end_datetime, self.string_rep))

#     def __eq__(self, other) -> bool:
#         self.start_datetime == other.start_datetime

def merge_ics(in_filepath, out_filepath):
    '''
    Take as input a list of strings indicating filepaths to .ics files and merges the events
    in each .ics file into one large .ics file, that is written to out_filepath.

    Future Changes:
    1) Return a string/list representation of the .ics file instead of creating a new
    .ics file.

    :param in_filepath: A list containing filepaths (as strings) to .ics files
    :param out_filepath: A string indicating the filepath that the output .ics file will be created
    '''
    calxs = ["BEGIN:VCALENDAR\n"]
    for filepath in in_filepath:
        with open(filepath) as f:
            intermediate = []
            take = False
            for line in f:
                if line == "END:VEVENT\n":
                    take = False
                    intermediate.append(line)
                elif line == "BEGIN:VEVENT\n":
                    take = True
                    intermediate.append(line)
                # elif line[:7] == "DTSTART":
                #     # perform checks
                #     pass
                # elif line[:5] == "DTEND":
                #     # perform checks
                #     pass
                else:
                    if take:
                        intermediate.append(line)
            calxs.extend(intermediate)
        f.close()
    calxs.append("END:VCALENDAR")

    f = open(out_filepath, 'w')
    for line in calxs:
        f.write(line)
    f.close()

def parse_output_ics(in_filepath):
    '''
    Takes as input a filepath to a .ics file and returns a list of events in the ics file,
    represented as lists of [start_datetime, end_datetime], sorted in ascending order
    by start_datetime

    Issues: 
    1) Currently does not work on recurring events
    2) Currently does not deal with events where end_datetime does not exist
    
    Future changes:
    1) Change the input to be a string representing an .ics file rather than a filepath

    :param in_filepath: A string representing the filepath of the .ics file to be parsed
    :returns: A sorted list of events, with each event represented as a list containing 
                a start datetime object and end datetime object
    '''
    events_list = []
    with open(in_filepath) as f:
        # Temp container for start date
        start_date_temp = None
        
        for line in f:
            # When start datetime found
            if line.split(":")[0] == "DTSTART":
                start_date = line.split(":")[1].strip()
                
                # Deal with UTC dates
                if start_date[-1] == "Z":
                    start_date = start_date[:-1]
                
                # Parse date
                start_date_temp = datetime.strptime(start_date, "%Y%m%dT%H%M%S")

            # When end datetime found
            elif line.split(":")[0] == "DTEND":
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
 
def filter(events_list, start_date, end_date):
    '''
    Takes a list of events represented as a list of lists containing start and end datetime objects,
    and returns a filtered list of events that occur between the given start and end date only.

    :param events_list: A list of events represented as a list of lists containing start and end datetime objects.
    :param start_date: A datetime object representing the start of the user's desired search space.
    :param end_date: A datetime object representing the end of the user's desired search space.
    :returns: A list of events that occur between the user's provided start and end date inclusive.
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
    
    return filtered

def daterange(start_date, end_date):
    '''
    Takes as input a start and end date and iterates through each date.

    :param start_date: The datetime object representing the start date.
    :param end_date: The datetime object representing the end date.
    :returns: A generator that allows for iteration between the provided start and end date
    '''
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)

def find_free_time(in_filepath, start_datetime, end_datetime, min_hourly_interval):
    '''
    Given a list of filepaths to .ics files, prints out common free times of at least the minimum user provided
    interval for each day between the user's provided start and end date.

    Future Changes:
    1) Might have to return the dictionary in future (Tentative).

    :param in_filepath: A list of strings representing filepaths to .ics files.
    :param start_datetime: A datetime object that represents the start date of the user's desired search space.
    :param end_datetime: A datetime object that represents the end date of the user's desired search space.
    :param min_hourly_interval: A number denoting the minimum number of hours for a block of common free time to be considered valid.
    '''
    merge_ics(in_filepath, 'out.ics')
    events = filter(parse_output_ics('out.ics'), start_datetime, end_datetime)
    
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
        free_time_dict[date] = [True for i in range(23)]
    
    for event in events:
        event_start_date = event[0].date()
        event_end_date = event[1].date()
        event_start_time = event[0].time().hour
        cond = event[1].time().minute > 0 or event[1].time().second > 0 or event[1].time().microsecond > 0
        event_end_time = (event[1].time().hour + 1) if (cond) else event[1].time().hour

        # Case 1: Start and end date are the same
        if (event_start_date == event_end_date):
            temp = free_time_dict[event_start_date]
            for i in range(event_start_time, event_end_time + 1):
                temp[i] = False
        
        # Case 2: Start and end date are different
        else:
            # Label all dates between start exclusive and end exclusive to be false
            for date in daterange(event_start_date + timedelta(days=1), event_end_date):
                free_time_dict[date] = [False for i in range(23)]
            
            # Look only at start and end dates and label accordingly
            temp = free_time_dict[event_start_date]
            for i in range(event_start_time, 24):
                temp[i] = False

            temp = free_time_dict[event_end_date]
            for i in range(0, event_end_time + 1):
                temp[i] = False
    
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

    print(final_results)    

if __name__ == '__main__':
    start = datetime(2021, 1, 11, 0, 0, 0)
    end = datetime(2021, 3, 16, 18, 0, 0)
    find_free_time(['./test ics files/nay.ics', './test ics files/pat.ics'], start, end, 5)