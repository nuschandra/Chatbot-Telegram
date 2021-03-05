from flask import Flask, request
import telegram
from pymongo import MongoClient
import bert_detection
import database_updates

app = Flask(__name__)

bot_token = "1537657914:AAEspo0IA7tiW2CCAnWLfsxOd0YabGC-r50"
bot_username = "VirtualRecruiterBot"
bot_url = "https://43af60ebad91.ngrok.io/" ## old url but works without 
bot = telegram.Bot(token=bot_token)
bot.delete_webhook(drop_pending_updates=True)
bot_url =  "https://77553db97b21.ngrok.io/"
bot.setWebhook('{URL}{HOOK}'.format(URL=bot_url, HOOK=bot_token))


def get_schedule(bot,chat_id,sch_list):
    button_list = []
    for cn,objid,sch in sch_list:
        dic ={"type" : "show_confirm", "sce_id" : objid } 
        button_list.append(InlineKeyboardButton(cn+" "+sch,callback_data=str(dic)))
       
    button_list  = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    reply_markup=InlineKeyboardMarkup(button_list)
    bot.send_message(chat_id=chat_id, text='Schedule :',reply_markup=reply_markup)
    return

def show_confirm(bot,chat_id, context):
    yes={"type" : "delete_sce",  "sce_id" : context['sce_id'] } 
    no={"type" : "exit"} 
    button_list=[
        InlineKeyboardButton('Cancel',callback_data=str(no)),
        InlineKeyboardButton('Confirm',callback_data=str(yes))
    ]
    button_list  = [button_list[i:i + 2] for i in range(0, len(button_list), 2)]
    reply_markup=InlineKeyboardMarkup(button_list)
    bot.send_message(chat_id=chat_id, text='Choose from the following',reply_markup=reply_markup)
    return

def delete_sce(bot,chat_id, context):
    bot.send_message(chat_id=chat_id, text = context['sce_id'])
    return

def exit_bot(bot,chat_id, context):
    bot.send_message(chat_id=chat_id, text="exit")
    return
    
def handle_callback(bot,update):
    chat_id = update.callback_query.message.chat.id
    msg_id = update.callback_query.message.message_id
    
    context = ast.literal_eval(update.callback_query.data)
    if(context['type']=="show_confirm"):
        show_confirm(bot,chat_id,context)
    elif(context['type']=="delete_sce"):
        delete_sce(bot,chat_id,context)
    elif(context['type']=="exit"):
        exit_bot(bot,chat_id,context)
    return


def handle_call(bot,update):
    print(update)
    chat_id = update.message.chat.id
    msg_id = update.message.message_id
    first_name = update.message.chat.first_name
    text = update.message.text.encode('utf-8').decode()
    
    print("got text message :", text)

    if(text=="/start"):
        welcome_msg = "Welcome!"
        bot.sendMessage(chat_id=chat_id, text=welcome_msg, reply_to_message_id=msg_id)

    else:
        response,intent = bert_detection.chat(update)
        print(response)    
    
        if intent == 'schedule_list':
            sch_list = [("Candidate Name1","602a22d7829ac6fe97dc7b93","May 12, 4pm"),
                        ("Candidate Name2","602a2332829ac6fe97dc7b95","Dec 2, 5pm"),
                        ("Candidate Name3","602a2af515fb6f9e7a3e7d6f","Mar 12, 2pm")]
            get_schedule(bot,chat_id,sch_list)
        bot.sendMessage(chat_id=chat_id, text=response, reply_to_message_id=msg_id)    
    return

@app.route("/{}".format(bot_token), methods = ['POST'])
def process_input_message():    
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    
    if update.callback_query is not  None:
       handle_callback(bot,update)
    else:
        handle_call(bot, update)
    return 'ok'
    # update = telegram.Update.de_json(request.get_json(force=True), bot)

    # chat_id = update.message.chat.id
    # msg_id = update.message.message_id
    # first_name = update.message.chat.first_name
    # print(update)
    # # Telegram understands UTF-8, so encode text for unicode compatibility
    # text = update.message.text.encode('utf-8').decode()
    # # for debugging purposes only
    # print("got text message :", text)

    # if(text=="/start"):
    #     welcome_msg = "Welcome!"
    #     bot.sendMessage(chat_id=chat_id, text=welcome_msg, reply_to_message_id=msg_id)
    # else:
    #     response,intent = bert_detection.chat(update)
    #     print(response)
        
    #     bot.sendMessage(chat_id=chat_id, text=response, reply_to_message_id=msg_id)
    
    # return 'ok'
    
# @app.route('/set_webhook', methods=['GET', 'POST'])
# def set_webhook():
#     print("Inside setting webhook")
#     s = bot.setWebhook('{URL}{HOOK}'.format(URL=bot_url, HOOK=bot_token))
#     if s:
#         return "webhook setup ok"
#     else:
#         return "webhook setup failed"

# @app.route('/delete_webhook', methods=['GET'])
# def delete_webhook():
#     print("Inside deleting webhook")
#     s = bot.delete_webhook(drop_pending_updates=True)
#     if s:
#         return "webhook deleted"
#     else:
#         return "webhook delete failed"

# @app.route('/runMongo', methods=['GET'])
# def run_mongo():
#     print("YOOOOOO")
#     try:
#         myclient =  MongoClient("mongodb+srv://user:user@cluster0.oklqw.mongodb.net/test")
#         mydb = myclient["plp_project"]
#         mycol = mydb["resume_details"]
#         print(mycol.find_one())
#     except Exception as e:
#         print(e) 

if __name__ == "__main__":
    app.run(threaded=True)