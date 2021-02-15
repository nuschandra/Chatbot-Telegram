from pymongo import MongoClient

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