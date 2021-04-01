import random
import tensorflow as tf
from tensorflow import keras
from bert import BertModelLayer
from bert.tokenization.bert_tokenization import FullTokenizer
import numpy as np
import json
import database_updates
from datetime import datetime
import tzlocal
import requests
import urllib.request
import slot_detection
from bson import ObjectId
import uuid
import os
import spacy_ner_detection
import recommendation
import string

model = keras.models.load_model("bert_intent_detection.hdf5",custom_objects={"BertModelLayer": BertModelLayer},compile=False)

tokenizer = FullTokenizer(vocab_file="vocab.txt")
classes = ['greetings', 'hiring_request', 'goodbye', 'schedule_list', 'bot_skill', 'update_performance']
print(classes)

with open('intents.json') as file:
    data = json.load(file)

def chat(inp):
    print(inp)
    user_text = inp.message.text.encode('utf-8').decode()
    sentences=[user_text]
    pred_tokens = map(tokenizer.tokenize, sentences)
    pred_tokens = map(lambda tok: ["[CLS]"] + tok + ["[SEP]"], pred_tokens)
    pred_token_ids = list(map(tokenizer.convert_tokens_to_ids, pred_tokens))

    pred_token_ids = map(lambda tids: tids +[0]*(21-len(tids)),pred_token_ids)
    pred_token_ids = np.array(list(pred_token_ids))
    predictions = model.predict(pred_token_ids)
    predictions_index=predictions.argmax(axis=-1)
    final_intent=''
    #if (predictions[predictions_index] < 0.9):
    #    final_intent = "unknown"
    #    response = "Sorry, I did not understand what you meant there."
    #    return response, final_intent

    for text, label in zip(sentences, predictions_index):
        confidence = predictions[0][label]
        if (confidence < 0.9):
            final_intent = "unknown"
            response = "Sorry, I did not understand what you meant there."
            return response, final_intent

        final_intent=classes[label]
        print("text:", text, "\nintent:", classes[label])
        print()
    
        response = getCorrectResponse(inp, final_intent)
    
    return response,final_intent


def getCorrectResponse(inp, final_intent):
    date_of_msg = get_current_date(inp)

    first_name = inp.message.chat.first_name
    chat_id = inp.message.chat.id
    user_text = inp.message.text.encode('utf-8').decode()
  
    
    for tg in data["intents"]:
        if tg['tag'] == final_intent:
            if final_intent == 'greetings':
                if (database_updates.get_record_by_chat_id_and_date(date_of_msg,chat_id)):
                    responses = random.choice(tg['secondary_responses']).format(first_name)
                else:
                    responses = random.choice(tg['primary_responses'])
            elif final_intent == 'schedule_list':
                responses = slot_detection.schedule_list(user_text, chat_id)
            elif final_intent == 'update_performance':
                responses = database_updates.find_completed_interviews(chat_id)
            else:
                responses = random.choice(tg['responses'])

    database_updates.insert_chatbot_user_data(date_of_msg,first_name,chat_id,final_intent)
    return responses

def process_file(file_id,bot_token):
    url = "https://api.telegram.org/bot"+bot_token+"/getFile?file_id="+file_id
    r = requests.get(url)
    data = r.json()
    file_path = data['result']['file_path']
    download_url = "https://api.telegram.org/file/bot"+bot_token+"/"+file_path
    response = urllib.request.urlopen(download_url)
    job_id=''.join(random.choices(string.ascii_letters + string.digits, k=16))
    file_name = job_id + ".txt"

    directory = os.getcwd()
    jd_file = os.path.join(directory,"job_descriptions/"+file_name)
    file = open(jd_file, 'wb')
    file.write(response.read())
    file.close()
    return jd_file, job_id

def save_jd_in_database(jd_file,job_id,chat_id):
    jd_dict = recommendation.extract_jd_details(jd_file)
    if 'Title' not in jd_dict.keys():
        title=='N/A'
    else:
        title=jd_dict['Title'][0]

    try:
        database_updates.save_job_description(job_id,chat_id,"OPEN",title.lower())
    except Exception as e:
        raise e

def trigger_resume_fetching(jd_file,job_id,chat_id):
    #extracted_jd = spacy_ner_detection.extract_jd_details(jd_file,job_id)

    ## RUN WORD2VEC/TF-IDF at this point to obtain suitable resumes
    recommended_resumes=recommendation.trigger_resume_fetching(jd_file,job_id,chat_id)
    resume_info = []
    max_count=0
    for resume in recommended_resumes:
        resume_file_name=resume[-36:-4]
        candidate_details = {}
        candidate_details['resume_doc']=resume_file_name
        candidate_details['name'],candidate_details['email'],candidate_details['id']=database_updates.get_candidate_name_email_id(resume_file_name)
        candidate_id=candidate_details['id']
        job_title=database_updates.get_job_title_based_on_jobid(job_id)
        date,time,status=check_duplicate_interview(chat_id,candidate_id,job_title)
        states_not_to_return=['interview_scheduled','Candidate Hired','Candidate Rejected']
        if status in states_not_to_return:
            continue
        resume_info.append(candidate_details)    
        max_count+=1
        if(max_count==3):
            break
    return resume_info

def get_current_date(inp):
    unix_timestamp = inp.message.date.timestamp()
    local_timezone = tzlocal.get_localzone()
    local_time = datetime.fromtimestamp(unix_timestamp, local_timezone)
    date_of_msg = local_time.strftime("%d/%m/%Y")
    return date_of_msg
    
def check_duplicate_interview(chat_id,candidate_id,job_title):
    date,time,status= database_updates.get_interview_details_manager_candidate_id_title(chat_id,candidate_id,job_title)
    
    return date,time,status
        
def check_candidate_availability(selected_date,selected_time,candidate_id):
    candidate_interview_dates = database_updates.get_candidate_busy_dates(candidate_id)
    if (len(candidate_interview_dates)==0):
        return True
    else:
        for dates in candidate_interview_dates:
            db_date=dates["interview_date"].strftime(
                                    '%B') + " " + dates["interview_date"].strftime('%d')
            if (selected_date==db_date):
                db_time=dates["interview_time"]
                if(selected_time==db_time):
                    return False
                else:
                    continue
            else:
                continue
        return True

def check_manager_availability(selected_date,selected_time,manager_id):
    manager_interview_dates = database_updates.get_manager_busy_dates(manager_id)
    if (len(manager_interview_dates)==0):
        return True
    else:
        for dates in manager_interview_dates:
            db_date=dates["interview_date"].strftime(
                                    '%B') + " " + dates["interview_date"].strftime('%d')
            if (selected_date==db_date):
                db_time=dates["interview_time"]
                if(selected_time==db_time):
                    return False
                else:
                    continue
            else:
                continue
        return True

