from pymongo import MongoClient
from datetime import timedelta
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
            elif i['type'] == 'TIME':
                try:
                    date = date+i['value'][len(date):]
                except NameError:
                    date = i['value']
            elif i['type'] == 'DURATION' and type(i['value']) == dict:
                date = date+i['value']['begin']
            elif i['type'] == 'DURATION' and len(i['value']) == 10:
                date = i['value'][:10]

        if 'INTERSECT' in date and len(sutime.parse(text)) != 0:
            date = date[:10]+date[date.find('(')+1:date.find('(')+7]
        date = parse(date)
    except:
        date = datetime.now()

    return(date)


myclient = MongoClient(
    "mongodb+srv://user:user@cluster0.oklqw.mongodb.net/test")
mydb = myclient["plp_project"]
mycol = mydb["resume_details"]
lakcol = mydb["interview_details"]


def schedule_list(text, chat_id):
    text = text.lower()
    try:
        sutime = SUTime(mark_time_ranges=True, include_range=True)
        entity_extractor = sutime.parse(text)
        print(entity_extractor)
        if lakcol.find_one({'manager_id': chat_id}):
            if entity_extractor == []:
                lst = []
                for entry in lakcol.find({'manager_id': chat_id}):
                    date = entry["interview_date"].strftime(
                        '%B') + ", " + entry["interview_date"].strftime('%d')
                    time = entry["interview_time"]
                    candidate_id = entry["candidate_id"]
                    dbid = entry["_id"]
                    for entry in mycol.find({'_id': candidate_id}):
                        name = entry["Name"]
                        email = entry["Email"]
                        lst.append((name + " ", str(dbid), "  " +
                                    date + "  " + str(time)))
                return lst
            for ent in entity_extractor:
                slot = ent["value"]
                if ent["type"] == "DATE" and len(ent["value"]) == 8:
                    slot = datetime.strptime(slot + '-1', '%G-W%V-%u')
                    slot_start = datetime.strftime(slot, '%Y-%m-%d')
                    slot_break_start = slot_start.split("-")
                    sy, sm, sd = slot_break_start
                    slot_end = slot + timedelta(days=6)
                    slot_end = datetime.strftime(slot_end, '%Y-%m-%d')
                    slot_break_end = slot_end.split("-")
                    ey, em, ed = slot_break_end
                    sy, sm, sd, ey, em, ed = int(sy), int(
                        sm), int(sd), int(ey), int(em), int(ed)
                    start = datetime(sy, sm, sd, 0, 0, 0, 0)
                    end = datetime(ey, em, ed, 23, 59, 59, 99999)
                    count = lakcol.find(
                        {'interview_date': {'$lt': end, '$gte': start}}).count()
                    if count >= 1:
                        lst = []
                        for entry in lakcol.find({'interview_date': {'$lt': end, '$gte': start}}):
                            if entry["manager_id"] == chat_id:
                                date = entry["interview_date"].strftime(
                                    '%B') + ", " + entry["interview_date"].strftime('%d')
                                time = entry["interview_time"]
                                candidate_id = entry["candidate_id"]
                                dbid = entry["_id"]
                                for entry in mycol.find({'_id': candidate_id}):
                                    name = entry["Name"]
                                    email = entry["Email"]
                                    lst.append(
                                        (name + " ", str(dbid), "  " + date + "  " + str(time)))
                        return lst
                    else:
                        return(f"No interviews found for {ent['text']}")
                elif ent["type"] == "DATE" and len(ent["value"]) == 7:
                    slot = slot + "-01"
                    slot_break = slot.split("-")
                    sy, sm, sd = slot_break
                    ey, em = sy, sm

                    class Solution(object):
                        def numberOfDays(self, y, m):
                            leap = 0
                            if y % 400 == 0:
                                leap = 1
                            elif y % 100 == 0:
                                leap = 0
                            elif y % 4 == 0:
                                leap = 1
                            if m == 2:
                                return 28 + leap
                            list = [1, 3, 5, 7, 8, 10, 12]
                            if m in list:
                                return 31
                            return 30
                    ob1 = Solution()
                    ed = str(ob1.numberOfDays(int(sy), int(sm)))
                    sy, sm, sd, ey, em, ed = int(sy), int(
                        sm), int(sd), int(ey), int(em), int(ed)
                    start = datetime(sy, sm, sd, 0, 0, 0, 0)
                    end = datetime(ey, em, ed, 23, 59, 59, 99999)
                    count = lakcol.find(
                        {'interview_date': {'$lt': end, '$gte': start}}).count()
                    if count >= 1:
                        lst = []
                        for entry in lakcol.find({'interview_date': {'$lt': end, '$gte': start}}):
                            if entry["manager_id"] == chat_id:
                                date = entry["interview_date"].strftime(
                                    '%B') + ", " + entry["interview_date"].strftime('%d')
                                time = entry["interview_time"]
                                candidate_id = entry["candidate_id"]
                                dbid = entry["_id"]
                                for entry in mycol.find({'_id': candidate_id}):
                                    name = entry["Name"]
                                    email = entry["Email"]
                                    lst.append(
                                        (name + " ", str(dbid), "  " + date + "  " + str(time)))
                        return lst
                    else:
                        return(f"No interviews found for {ent['text']}")
                elif ent["type"] == "DURATION":
                    today = datetime.now()
                    year = today.year
                    slot_break_begin = slot["begin"].split("-")
                    slot_break_end = slot["end"].split("-")
                    slot_break_begin[0] = slot_break_end[0] = year
                    sy, sm, sd = slot_break_begin
                    ey, em, ed = slot_break_end
                    sy, sm, sd, ey, em, ed = int(sy), int(
                        sm), int(sd), int(ey), int(em), int(ed)
                    start = datetime(sy, sm, sd, 0, 0, 0, 0)
                    end = datetime(ey, em, ed, 23, 59, 59, 99999)
                    count = lakcol.find(
                        {'interview_date': {'$lt': end, '$gte': start}}).count()
                    if count >= 1:
                        lst = []
                        for entry in lakcol.find({'interview_date': {'$lt': end, '$gte': start}}):
                            if entry["manager_id"] == chat_id:
                                date = entry["interview_date"].strftime(
                                    '%B') + ", " + entry["interview_date"].strftime('%d')
                                time = entry["interview_time"]
                                candidate_id = entry["candidate_id"]
                                dbid = entry["_id"]
                                for entry in mycol.find({'_id': candidate_id}):
                                    name = entry["Name"]
                                    email = entry["Email"]
                                    lst.append(
                                        (name + " ", str(dbid), "  " + date + "  " + str(time)))
                        return lst
                    else:
                        return(f"No interviews found {ent['text']}")
                else:
                    print("I am in the method for dates such as 28-03-2021")
                    slot_break = slot.split("-")
                    sy, sm, sd = slot_break
                    ey, em, ed = sy, sm, sd
                    sy, sm, sd, ey, em, ed = int(sy), int(
                        sm), int(sd), int(ey), int(em), int(ed)
                    start = datetime(sy, sm, sd, 0, 0, 0, 0)
                    end = datetime(ey, em, ed, 23, 59, 59, 99999)
                    count = lakcol.find(
                        {'interview_date': {'$lt': end, '$gte': start}}).count()

                    if count >= 1:
                        print("There is a hit in the database")
                        lst = []
                        for entry in lakcol.find({'interview_date': {'$lt': end, '$gte': start}}):
                            print("There is one interview to be returned")
                            if entry["manager_id"] == chat_id:
                                date = entry["interview_date"].strftime(
                                    '%B') + " " + entry["interview_date"].strftime('%d')
                                time = entry["interview_time"]
                                candidate_id = entry["candidate_id"]
                                dbid = entry["_id"]
                                for entry in mycol.find({'_id': candidate_id}):
                                    name = entry["Name"]
                                    email = entry["Email"]
                                    lst.append(
                                        (name + " ", str(dbid), "  " + date + "  " + str(time)))
                        return lst
                    else:
                        return(f"No interviews found for {ent['text']}")
        else:
            return("You have no interviews scheduled at the moment.")
    except Exception as exception:
        print(exception)
        return("Sorry, I could not understand that. Please check for any spelling errors or Please rephrase the question. If either doesn't work, please reach out to the support at abc@gmail.com for assistance.")
