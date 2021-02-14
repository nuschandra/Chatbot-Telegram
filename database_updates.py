from pymongo import MongoClient

myclient =  MongoClient("mongodb+srv://user:user@cluster0.oklqw.mongodb.net/test")
mydb = myclient["plp_project"]

def insert_chatbot_user_data(name,chat_id,status):
    schema = mydb["chatbot_user_details"]
    data = { "chat_id": chat_id, "name": name, "status":status }
    x = schema.insert_one(data)
    print(x.inserted_id)