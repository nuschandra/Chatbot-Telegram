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

def save_job_description(jd_id, chat_id, status,title):
    schema = mydb["jd_collection"]
    data = {"created_date":datetime.now(), "manager_id": chat_id, "job_id": jd_id, "status":status,"job_title":title}
    myquery={'manager_id':chat_id,'job_title':title,'status':'OPEN'}
    existing_jd=schema.find_one(myquery)
    if(existing_jd!=None):
        raise Exception("You already have a job opening for this role")
    schema.insert_one(data)

def get_candidate_name_email_id(candidate_id):
    schema = mydb["resume_details"]
    candidate= schema.find_one({"Resume_Doc":candidate_id})
    if(candidate==None):
        return None,None,None
    return candidate['Name'], candidate['Email'],str(candidate['_id'])

def save_interview_date(selected_date,candidate_id,manager_id,job_id,status):
    can_id = ObjectId(candidate_id)
    schema = mydb["interview_details"]
    title = get_job_title_based_on_jobid(job_id)
    myquery={'job_id':job_id,'candidate_id':candidate_id}
    existing_time_slot=schema.find_one(myquery)
    if(existing_time_slot==None):
        data = {"created_date":datetime.now(), "manager_id": manager_id, "interview_date": selected_date, "status":status, "candidate_id":can_id,"job_id":job_id,"job_title":title,"interview_time":"N/A"}
        oid = schema.insert_one(data)
    else:
        updated_values = {"$set": {"interview_date":selected_date,"interview_time":"N/A"}}
        oid=schema.update_one(myquery,updated_values)

    return str(oid.inserted_id)

def save_interview_time(selected_time,interview_oid):
    schema = mydb["interview_details"]
    print(interview_oid)
    interview_id=ObjectId(interview_oid)
    myquery = {"_id":interview_id}
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
    if(interview_info==None):
        raise Exception("Your request is invalid. You might have already clicked on this candidate's button and duplicate requests are not permitted. If you would like to reschedule an interview, kindly request me to list interviews on a given date.")
    date = interview_info["interview_date"].strftime(
                                    '%B') + " " + interview_info["interview_date"].strftime('%d')
    time = interview_info["interview_time"]
    candidate_id=ObjectId(interview_info["candidate_id"])
    title=interview_info['job_title']
    schema=mydb["resume_details"]
    myquery = {"_id":candidate_id}
    resume_info= schema.find_one(myquery)
    name=resume_info["Name"]

    return name,date,time,title,str(candidate_id)

def get_interview_details_manager_candidate_id_title(manager_id,candidate_id,title):
    schema = mydb["interview_details"]
    can_id=ObjectId(candidate_id)
    myquery = {"manager_id":manager_id,"candidate_id":can_id,"job_title":title}
    interview_info= schema.find_one(myquery)

    if(interview_info!=None):
        if(interview_info['interview_date']=='N/A'):
            date='N/A'
        else:
            date = interview_info["interview_date"].strftime(
                                    '%B') + " " + interview_info["interview_date"].strftime('%d')
        time = interview_info["interview_time"]
        status= interview_info['status']
        return date,time,status
    else:
        return None,None,None
    
def get_job_title_based_on_jobid(job_id):
    schema = mydb["jd_collection"]
    myquery={"job_id":job_id}
    job_info= schema.find_one(myquery)

    if(job_info!=None):
        title=job_info["job_title"]
        return title
    else:
        raise Exception("There is some database corruption")

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

def find_completed_interviews(manager_id):
    # dd/mm/YY
    today_date = date.today().strftime("%d-%m-%Y")
    schema = mydb["interview_details"]
    slot_break = today_date.split("-")
    sd, sm, sy = slot_break
    sy, sm, sd = int(sy), int(sm), int(sd)
    start = datetime(sy, sm, sd, 0, 0, 0, 0)
    completed_interviews = list(schema.find({'interview_date': {'$lt': start},'status':'interview_scheduled','manager_id':manager_id}))

    current_day_interviews = list(schema.find({'interview_date': {'$eq': start},'status':'interview_scheduled','manager_id':manager_id}))
    for interview in current_day_interviews:
        interview_time = interview['interview_time']
        if(compare_am_pm_times(interview_time)):
            completed_interviews.append(interview)

    return completed_interviews

def compare_am_pm_times(interview_time):
    current_time = datetime.now().strftime("%I:%M%p")  # current_time ="12:00PM"
    if interview_time[5:7].lower() == 'AM'.lower() and current_time[5:7].lower() == 'PM'.lower():
        return True
    elif interview_time[5:7].lower() == 'PM'.lower() and current_time[5:7].lower() == 'AM'.lower():
        return False
    else:  # same part of day
        if(interview_time[0:2] == "12"):
            interview_time = "00" + ":" + interview_time[3:7]

        if(current_time[0:2] == "12"):
            current_time = "00" + ":" + current_time[3:7]

        if int(interview_time[0:2]) < int(current_time[0:2]):  # compare Hour
            return True
        elif int(interview_time[0:2]) > int(current_time[0:2]):
            return False
        else:
            if int(interview_time[3:5]) < int(current_time[3:5]):  # compare Minute
                return True
            elif int(interview_time[3:5]) > int(current_time[3:5]):
                return False
            else:
                return False

def update_hiring_status(object_id,status):
    interview_obj_id = ObjectId(object_id)
    schema = mydb["interview_details"]
    myquery = {"_id":interview_obj_id,"status":"interview_scheduled"}
    interview_to_update= schema.find_one(myquery)
    if (interview_to_update != None):
        updated_values = {"$set": {"status":status}}
        schema.update_one(myquery,updated_values)
        return True
    else:
        return False

def save_candidate(name,email,linkedin_contact,file_name,want_email_flag):
    schema = mydb["resume_details"]
    
    data = {"Name":name,"Email": email, "LinkedInContact":linkedin_contact, "Status": "RESUME_UPLOADED", "Resume_Doc": file_name,"want_email_flag":want_email_flag}
    myquery = {"LinkedInContact": linkedin_contact}
    existing_user = list(schema.find(myquery))
    if (len(existing_user) == 0):
        schema.insert_one(data)
        return True
    else:
        return False

def get_open_jd():
    schema = mydb["jd_collection"]
    return list(map(lambda val: (val['manager_id'], val['job_id'],val['job_title']), schema.find({'status': "OPEN" })))

def get_job_info_from_interview_obj_id(interview_oid):
    schema = mydb['interview_details']
    myquery={"_id":ObjectId(interview_oid)}
    interview = schema.find_one(myquery)
    return interview['job_id'],interview['job_title']
    
def close_job(job_id):
    schema = mydb['jd_collection']
    myquery={"job_id":job_id}
    interview = schema.find_one(myquery)
    if (interview != None):
        updated_values = {"$set": {"status":"CLOSED"}}
        schema.update_one(myquery,updated_values)

def reject_pending_candidates(job_id,chat_id):
    schema = mydb['interview_details']
    myquery={"job_id":job_id,"manager_id":chat_id,"status":"interview_scheduled"}
    updated_values = {"$set": {"status":"Candidate Rejected"}}
    
    pending_candidates = list(schema.find(myquery))
    if (len(pending_candidates) == 0):
        return
    else:
        schema.update_many(myquery,updated_values)

def get_candidate_busy_dates(candidate_id):
    schema=mydb['interview_details']
    candidate_id=ObjectId(candidate_id)
    myquery={'candidate_id':candidate_id,'status':'interview_scheduled'}
    candidate_interviews=list(schema.find(myquery))
    return candidate_interviews

def get_manager_busy_dates(manager_id):
    schema=mydb['interview_details']
    myquery={'manager_id':manager_id,'status':'interview_scheduled'}
    manager_interviews=list(schema.find(myquery))
    return manager_interviews

def check_if_candidate_hired(candidate_id):
    schema=mydb['interview_details']
    candidate_id=ObjectId(candidate_id)
    myquery={'candidate_id':candidate_id,'status':'Candidate Hired'}
    interview_details = schema.find_one(myquery)
    if (interview_details!=None):
        return True
    else:
        return False

def get_all_candidates():
    schema=mydb['resume_details']
    return list(schema.find())

def check_if_candidate_in_interview_details_table(candidate_id):
    schema=mydb['interview_details']
    myquery={'candidate_id':candidate_id}
    interview_details=schema.find_one(myquery)
    if (interview_details!=None):
        return True
    else:
        return False

def get_all_managers():
    schema=mydb['chatbot_user_details']
    return list(schema.find())