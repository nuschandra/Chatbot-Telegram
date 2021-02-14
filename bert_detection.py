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
    predictions = model.predict(pred_token_ids).argmax(axis=-1)
    final_intent=''
    for text, label in zip(sentences, predictions):
        final_intent=classes[label]
        print("text:", text, "\nintent:", classes[label])
        print()
    
        response = getCorrectResponse(inp.message.date, final_intent)
    
    return random.choice(response),final_intent


def getCorrectResponse(msg_timestamp, final_intent):
    unix_timestamp = msg_timestamp.timestamp()
    local_timezone = tzlocal.get_localzone()
    local_time = datetime.fromtimestamp(unix_timestamp, local_timezone)
    print(local_time.strftime("%Y-%m-%d %H:%M:%S.%f%z (%Z)"))

    for tg in data["intents"]:
        if final_intent == 'greetings':
            responses = tg['primary_responses']
            return responses
        else:
            responses = tg['responses']
            return responses
