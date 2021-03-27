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

def process_file(file_id,chat_id,bot_token):
    url = "https://api.telegram.org/bot"+bot_token+"/getFile?file_id="+file_id
    r = requests.get(url)
    data = r.json()
    file_path = data['result']['file_path']
    download_url = "https://api.telegram.org/file/bot"+bot_token+"/"+file_path
    response = urllib.request.urlopen(download_url)
    job_id=str(uuid.uuid4().hex)
    file_name = job_id + ".pdf"

    directory = os.getcwd()
    jd_file = os.path.join(directory,"job_descriptions/"+file_name)
    file = open(jd_file, 'wb')
    file.write(response.read())
    file.close()
    database_updates.save_job_description(job_id,chat_id,"OPEN")
    return jd_file, job_id

def trigger_resume_fetching(jd_file,job_id):
    extracted_jd = spacy_ner_detection.extract_jd_details(jd_file,job_id)

    ## RUN WORD2VEC/TF-IDF at this point to obtain suitable resumes
    resume_info = []
    candidate_details = {}
    selected_id = 'a2aab2536cc54bd890bb6dff9519c13d'
    candidate_details['resume_doc']=selected_id
    candidate_details['name'],candidate_details['email'],candidate_details['id']=database_updates.get_candidate_name_email_id(selected_id)
    
    resume_info.append(candidate_details)
    
    return resume_info

def get_current_date(inp):
    unix_timestamp = inp.message.date.timestamp()
    local_timezone = tzlocal.get_localzone()
    local_time = datetime.fromtimestamp(unix_timestamp, local_timezone)
    date_of_msg = local_time.strftime("%d/%m/%Y")
    return date_of_msg
    
def check_duplicate_interview(chat_id,candidate_id):
    date,time= database_updates.get_interview_details_manager_candidate_id(chat_id,candidate_id)
    return date,time