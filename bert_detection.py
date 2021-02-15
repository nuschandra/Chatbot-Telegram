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

model = keras.models.load_model("bert_intent_detection.hdf5",custom_objects={"BertModelLayer": BertModelLayer},compile=False)

tokenizer = FullTokenizer(vocab_file="vocab.txt")
classes = ['greetings', 'hiring_request', 'goodbye', 'interview_schedule', 'schedule_list']
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
    print(predictions)
    predictions_index = predictions.argmax(axis=-1)
    final_intent=''

    if (predictions[predictions_index] < 0.9):
        final_intent = "unknown"
        response = "Sorry, I did not understand what you meant there."
        return response, final_intent
        
    for text, label in zip(sentences, predictions):
        final_intent=classes[label]
        print("text:", text, "\nintent:", classes[label])
        print()
    
        response = getCorrectResponse(inp, final_intent)
    
    return response,final_intent


def getCorrectResponse(inp, final_intent):
    unix_timestamp = inp.message.date.timestamp()
    local_timezone = tzlocal.get_localzone()
    local_time = datetime.fromtimestamp(unix_timestamp, local_timezone)
    date_of_msg = local_time.strftime("%B %d %Y")

    first_name = inp.message.chat.first_name
    chat_id = inp.message.chat.id

    for tg in data["intents"]:
        if tg['tag'] == final_intent:
            if final_intent == 'greetings':
                if (database_updates.get_record_by_chat_id_and_date(date_of_msg,chat_id)):
                    responses = random.choice(tg['secondary_responses']).format(first_name)
                else:
                    responses = random.choice(tg['primary_responses'])
            else:
                responses = random.choice(tg['responses'])

    database_updates.insert_chatbot_user_data(date_of_msg,first_name,chat_id,final_intent)
    return responses