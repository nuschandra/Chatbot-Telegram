from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId

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

        
def get_open_jd():
    schema = mydb["jd_collection"]
    return list(map(lambda val: (val['manager_id'], val['job_id']), schema.find({'status': "OPEN" })))

