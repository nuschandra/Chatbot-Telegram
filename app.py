from flask import Flask, request
import telegram
from pymongo import MongoClient
import bert_detection
import database_updates

app = Flask(__name__)

bot_token = "1621891888:AAHBvpvmFNJDQoDlpB3ImaBwdQHOGn5d0Pg"
bot_username = "TestVirtualRecruiterBot"
bot_url = "https://c53f5f38a8d6.ngrok.io/" #change this URL to your ngrok url
#https://c53f5f38a8d6.ngrok.io/set_webhook
bot = telegram.Bot(token=bot_token)

@app.route("/{}".format(bot_token), methods = ['POST'])
def process_input_message():
    update = telegram.Update.de_json(request.get_json(force=True), bot)

    chat_id = update.message.chat.id
    msg_id = update.message.message_id
    first_name = update.message.chat.first_name
    print(update)
    print(update['message'])
    print(update['message']['text'])
    if update['message']['text'] != None:
        print("I am inside text method")
        # Telegram understands UTF-8, so encode text for unicode compatibility
        text = update.message.text.encode('utf-8').decode()
        # for debugging purposes only
        print("got text message :", text)

        if(text=="/start"):
            welcome_msg = "Welcome!"
            bot.sendMessage(chat_id=chat_id, text=welcome_msg, reply_to_message_id=msg_id)
        else:
            response,intent = bert_detection.chat(update)
            print(response)
            bot.sendMessage(chat_id=chat_id, text=response, reply_to_message_id=msg_id)
    elif update['message']['document'] != None:
        print("I am inside document method")
        file_type = update.message.document.mime_type
        print("File type is:" + file_type)
        if(database_updates.check_user_status(chat_id)):
            if file_type != 'application/pdf':
                error_message = "Sorry, kindly make sure you upload a pdf document only."
                bot.sendMessage(chat_id=chat_id, text=error_message, reply_to_message_id=msg_id)
            else:
                file_id = update.message.document.file_id
                bert_detection.process_file(file_id,chat_id)
                response = "Thank you for uploading the job description. Our algorithm will identify and recommend the best suited candidates to you."
                bot.sendMessage(chat_id=chat_id, text=response, reply_to_message_id=msg_id)
        else:
            error_message = "Sorry, I did not understand what you meant there."
            bot.sendMessage(chat_id=chat_id, text=error_message, reply_to_message_id=msg_id)

    return 'ok'
    
@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    print("Inside setting webhook")
    s = bot.setWebhook('{URL}{HOOK}'.format(URL=bot_url, HOOK=bot_token))
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"

@app.route('/delete_webhook', methods=['GET'])
def delete_webhook():
    print("Inside deleting webhook")
    s = bot.delete_webhook(drop_pending_updates=True)
    if s:
        return "webhook deleted"
    else:
        return "webhook delete failed"

@app.route('/runMongo', methods=['GET'])
def run_mongo():
    print("YOOOOOO")
    try:
        myclient =  MongoClient("mongodb+srv://user:user@cluster0.oklqw.mongodb.net/test")
        mydb = myclient["plp_project"]
        mycol = mydb["resume_details"]
        print(mycol.find_one())
    except Exception as e:
        print(e) 

if __name__ == "__main__":
    app.run(threaded=True)