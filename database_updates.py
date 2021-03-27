from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
from datetime import date

myclient =  MongoClient("mongodb+srv://user:user@cluster0.oklqw.mongodb.net/test")
mydb = myclient["plp_project"]

def insert_chatbot_user_data(date_of_msg,name,chat_id,status):
    schema = mydb["chatbot_user_details"]
    data = {"date":date_of_msg, "chat_id": chat_id, "name": name, "status":status}
    myquery = {"chat_id": chat_id}
    existing_user = list(schema.find(myquery))
    print(existing_user)
    if (len(existing_user) == 0):
        schema.insert_one(data)
    else:
        updated_values = {"$set": data}
        schema.update_one(myquery,updated_values)

def get_record_by_chat_id_and_date(date_of_msg,chat_id):
    schema = mydb["chatbot_user_details"]
    myquery = {"chat_id": chat_id}
    existing_user = list(schema.find(myquery))
    print(len(existing_user))
    if (len(existing_user) == 0):
        return False
    else:
        last_convo_date = existing_user[0]['date']
        print("Database date = " + last_convo_date)
        print("Message date = " + date_of_msg)

        if last_convo_date == date_of_msg:
            return True
        else:
            return False

def check_user_status(chat_id):
    schema = mydb["chatbot_user_details"]
    myquery = {"chat_id": chat_id}
    existing_user = list(schema.find(myquery))
    print(existing_user)
    if (len(existing_user) == 0):
        return False
    else:
        status = existing_user[0]['status']
        print(status)
        if status == 'hiring_request':
            return True
        else:
            return False
        
def hire_request(candidate_id):
    schema = mydb["resume_details"]
    id = ObjectId(candidate_id)
    myquery = {"_id": id}
    ## join resume_details and interview_details fetch suitable candidates after jd upload
    candidate = list(schema.find(myquery))
    """ remove the following dummy data"""
    candidate_details = "Name: " + str(candidate[0]['Name']) + "\n" + "Email: " + str(candidate[0]['Email']) + "\n" + "Phone: " + str(candidate[0]['Number'])
    return candidate_details


def schedule_interview(candidate_id,interview_datetime,chat_id, status):
    schema = mydb["interview_details"]
    """
    to be removed 
    candidate_id is of ObjectId type which is a FK 
    """
    candidate_id = mydb["resume_details"].find_one()['_id']  ## ObjectId(candidate_id) ## if int 

    data = { "candidate_id": candidate_id, "interview_date":interview_datetime,"manager_id":chat_id, "created_date": datetime.now(), "status":status}
    x = schema.insert_one(data)
    ##x.acknowledgedtimestamp status 
    return(x.acknowledged)

def get_prev_intent(chat_id):
    schema = mydb["chatbot_user_details"]
    return schema.find_one({"chat_id":chat_id})['status']

def save_job_description(jd_id, chat_id, status):
    schema = mydb["jd_collection"]
    data = {"created_date":datetime.now(), "manager_id": chat_id, "job_id": jd_id, "status":status}
    schema.insert_one(data)

def get_candidate_name_email_id(candidate_id):
    schema = mydb["resume_details"]
    candidate= schema.find_one({"Resume_Doc":candidate_id})
    return candidate['Name'], candidate['Email'],str(candidate['_id'])

def save_interview_date(selected_date,candidate_id,manager_id,status):
    can_id = ObjectId(candidate_id)
    schema = mydb["interview_details"]
    data = {"created_date":datetime.now(), "manager_id": manager_id, "interview_date": selected_date, "status":status, "candidate_id":can_id}
    schema.insert_one(data)

def save_interview_time(selected_time,candidate_id,manager_id):
    can_id = ObjectId(candidate_id)
    schema = mydb["interview_details"]
    myquery = {"manager_id":manager_id,"candidate_id":can_id}
    interview_to_update= schema.find_one(myquery)
    if (interview_to_update != None):
        updated_values = {"$set": {"interview_time":selected_time}}
        schema.update_one(myquery,updated_values)

def cancel_schedule(oid):
    schema = mydb["interview_details"]
    result = schema.delete_one({'_id': ObjectId(oid)})
    return result

def get_candidate_and_interview_info(object_id):
    schema = mydb["interview_details"]
    interview_id = ObjectId(object_id)
    myquery = {"_id":interview_id}
    interview_info= schema.find_one(myquery)
    date = interview_info["interview_date"].strftime(
                                    '%B') + " " + interview_info["interview_date"].strftime('%d')
    time = interview_info["interview_time"]
    candidate_id=ObjectId(interview_info["candidate_id"])
    schema=mydb["resume_details"]
    myquery = {"_id":candidate_id}
    resume_info= schema.find_one(myquery)
    name=resume_info["Name"]

    return name,date,time

def get_interview_details_manager_candidate_id(manager_id,candidate_id):
    schema = mydb["interview_details"]
    can_id=ObjectId(candidate_id)
    myquery = {"manager_id":manager_id,"candidate_id":can_id}
    interview_info= schema.find_one(myquery)

    if(interview_info!=None):
        date = interview_info["interview_date"].strftime(
                                    '%B') + " " + interview_info["interview_date"].strftime('%d')
        time = interview_info["interview_time"]
        return date,time
    else:
        return None,None

def find_interviews_scheduled_for_the_day():
    # dd/mm/YY
    today_date = date.today().strftime("%d-%m-%Y")
    schema = mydb["interview_details"]
    slot_break = today_date.split("-")
    sd, sm, sy = slot_break
    ed, em, ey = sd, sm, sy
    sy, sm, sd, ey, em, ed = int(sy), int(sm), int(sd), int(ey), int(em), int(ed)
    start = datetime(sy, sm, sd, 0, 0, 0, 0)
    end = datetime(ey, em, ed, 23, 59, 59, 99999)
    list_of_interviews = list(schema.find({'interview_date': {'$lt': end, '$gte': start}}))
    return list_of_interviews

def get_candidate_info(candidate_id):
    can_id=ObjectId(candidate_id)
    schema = mydb["resume_details"]
    myquery = {"_id":can_id}
    candidate_info= schema.find_one(myquery)
    return candidate_info["Name"],candidate_info["Email"]