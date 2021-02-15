from sutime import SUTime
from datetime import datetime
from dateutil import relativedelta
from dateutil.parser import parse
sutime = SUTime(mark_time_ranges=True, include_range=True)

def schedule_slot_detection(text):
    try:
        for i in sutime.parse(text):
            if i['type'] == 'DATE':
                try:
                    date = i['value']+date[10:]
                except NameError:
                    date = i['value']
            elif  i['type'] == 'TIME':
                try:
                    date = date+i['value'][len(date):]
                except NameError:
                    date = i['value']
            elif i['type'] == 'DURATION' and type(i['value'])== dict:
                date = date+i['value']['begin']
            elif i['type'] == 'DURATION' and len(i['value'])==10:
                date = i['value'][:10]
        
        if 'INTERSECT' in date and len(sutime.parse(text))!=0:
            date = date[:10]+date[date.find('(')+1:date.find('(')+7]
        date = parse(date)
    except:
        date = datetime.now()
        
    return(date)