from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import telegram
from telegram import InlineKeyboardButton,InlineKeyboardMarkup
from pymongo import MongoClient
import telegram_message_processing
import database_updates
import ast
import os
import uuid
import spacy_ner_detection
import telegramcalendar
from datetime import datetime
import tzlocal

app = Flask(__name__)

bot_token = "1621891888:AAHBvpvmFNJDQoDlpB3ImaBwdQHOGn5d0Pg"
bot_username = "VirtualRecruiterBot"
bot_url = "https://b9e5a020b8d7.ngrok.io/"
bot = telegram.Bot(token=bot_token)
bot.delete_webhook(drop_pending_updates=True)
bot_url =  "https://b76d63888d2a.ngrok.io/"
bot.setWebhook('{URL}{HOOK}'.format(URL=bot_url, HOOK=bot_token))


def get_schedule(bot,chat_id,sch_list):
    button_list = []
    for cn,objid,sch in sch_list:
        dic ={"type" : "show_confirm", "sce_id" : objid } 
        button_list.append(InlineKeyboardButton(cn+" "+sch,callback_data=str(dic)))
       
    button_list  = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    reply_markup=InlineKeyboardMarkup(button_list)
    bot.send_message(chat_id=chat_id, text='This is your Schedule. Please select the the appointment from the following to confirm or cancel. :',reply_markup=reply_markup)
    return

def show_confirm(bot,chat_id, context):
    yes={"type" : "delete_sce",  "sce_id" : context['sce_id'] } 
    no={"type" : "cancel"} 
    button_list=[
        InlineKeyboardButton('Cancel',callback_data=str(no)),
        InlineKeyboardButton('Confirm',callback_data=str(yes))
    ]
    button_list  = [button_list[i:i + 2] for i in range(0, len(button_list), 2)]
    reply_markup=InlineKeyboardMarkup(button_list)
    bot.send_message(chat_id=chat_id, text='Confirm or Cancel.',reply_markup=reply_markup)
    return
    
def handle_callback(bot,update):
    chat_id = update.callback_query.message.chat.id
    msg_id = update.callback_query.message.message_id
    
    context = ast.literal_eval(update.callback_query.data)
    if(context['type']=="show_confirm"):
        bot.editMessageReplyMarkup(chat_id=chat_id, message_id=msg_id, reply_markup=None)
        show_confirm(bot,chat_id,context)
    elif(context['type']=="delete_sce"):
        bot.editMessageReplyMarkup(chat_id=chat_id, message_id=msg_id, reply_markup=None)
        bot.send_message(chat_id=chat_id, text = "Confirmed the appointment!")
    elif(context['type']=="cancel"):
        bot.editMessageReplyMarkup(chat_id=chat_id, message_id=msg_id, reply_markup=None)
        bot.send_message(chat_id=chat_id, text = "Cancelled the appointment!")
    elif(context['type']=="Accept"):
        bot.editMessageReplyMarkup(chat_id=chat_id, message_id=msg_id, reply_markup=None)
        show_calendar_for_interview(chat_id)
    elif(context['type']=="Reject"):
        bot.editMessageReplyMarkup(chat_id=chat_id, message_id=msg_id, reply_markup=None)
        bot.send_message(chat_id=chat_id, text = "Rejected candidate")
    elif(context['type']=='Date'):
        selected,date=telegramcalendar.process_calendar_selection(bot,update)
        if selected:
            local_timezone = tzlocal.get_localzone()
            today = datetime.now(local_timezone).date().strftime("%d/%m/%Y")
            current_selected_date = date.strftime("%d/%m/%Y")
            if (current_selected_date<=today):
                bot.send_message(chat_id=update.callback_query.from_user.id,
                        text="The date you've selected is invalid. Please choose a valid date.",
                        reply_markup=None)
                show_calendar_for_interview(chat_id)

            bot.send_message(chat_id=update.callback_query.from_user.id,
                        text="You selected %s" % (date.strftime("%d/%m/%Y")),
                        reply_markup=None)
            show_time_slots_for_interview(chat_id)
    elif(context['type']=='Time'):
        selected,time=telegramcalendar.process_time_selection(bot,update)
        if selected:
            bot.send_message(chat_id=update.callback_query.from_user.id,
                        text="Your interview has been scheduled at %s" % time % "",
                        reply_markup=None)
    return


def handle_call(bot,update):
    print(update)
    chat_id = update.message.chat.id
    msg_id = update.message.message_id

    if update['message']['text'] != None:
        
        first_name = update.message.chat.first_name
        text = update.message.text.encode('utf-8').decode()
        print("I am inside text method")

        # Telegram understands UTF-8, so encode text for unicode compatibility
        text = update.message.text.encode('utf-8').decode()
        # for debugging purposes only
        print("got text message :", text)
        
    
        if(text=="/start"):
            welcome_msg = "Welcome!"
            bot.sendMessage(chat_id=chat_id, text=welcome_msg, reply_to_message_id=msg_id)
    
        else:
            response,intent = telegram_message_processing.chat(update)
            print(response)    
        
            if intent == 'schedule_list':
            # if text == 'schedule_list':
                sch_list = [("Candidate Name1","602a22d7829ac6fe97dc7b93","May 12, 4pm"),
                            ("Candidate Name2","602a2332829ac6fe97dc7b95","Dec 2, 5pm"),
                            ("Candidate Name3","602a2af515fb6f9e7a3e7d6f","Mar 12, 2pm")]
                get_schedule(bot,chat_id,sch_list)
                response = "returned scheduledlist"
            bot.sendMessage(chat_id=chat_id, text=response, reply_to_message_id=msg_id) 
            
    elif update['message']['document'] != None:
        file_type = update.message.document.mime_type
        print("File type is:" + file_type)
        if(database_updates.check_user_status(chat_id)):
        # if (True):
            if file_type != 'application/pdf':
                error_message = "Sorry, kindly make sure you upload a pdf document only."
                bot.sendMessage(chat_id=chat_id, text=error_message, reply_to_message_id=msg_id)
            else:
                file_id = update.message.document.file_id
                jd_file,job_id = telegram_message_processing.process_file(file_id,chat_id,bot_token)
                response = "Thank you for uploading the job description. Our algorithm will identify and recommend the best suited candidates to you."
                bot.sendMessage(chat_id=chat_id, text=response, reply_to_message_id=msg_id)
                resume_info = telegram_message_processing.trigger_resume_fetching(jd_file,job_id)
                for info in resume_info:
                    ids=info['resume_doc']
                    name=info['name']
                    email=info['email']
                    file_to_send = "Resumes/"+str(ids)+".pdf"
                    #get_candidate_details = database_updates.hire_request(ids)
                    get_candidate_details = "Name: "+name+"\n"+"Email: "+email
                    accept={"type":"Accept","can_id":ids} 
                    reject={"type":"Reject","can_id":ids} 
                    keyboard = [[InlineKeyboardButton("Accept", callback_data=str(accept))],
                                [InlineKeyboardButton("Reject", callback_data=str(reject))]]    
                    bot.sendDocument(chat_id=chat_id,document=open(file_to_send, 'rb'),caption=get_candidate_details,reply_markup=InlineKeyboardMarkup(keyboard),filename=name+".pdf")

        else:
            error_message = "Sorry, I did not understand what you meant there."
            bot.sendMessage(chat_id=chat_id, text=error_message, reply_to_message_id=msg_id)
         
    
    return

@app.route("/{}".format(bot_token), methods = ['POST'])
def process_input_message():    
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    
    if update.callback_query is not  None:
        handle_callback(bot,update)
    else:
        handle_call(bot, update)

    return 'ok'

@app.route("/resumeUpload", methods=["GET","POST"])
def upload_resume():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        if uploaded_file.filename != '':
            directory = os.getcwd()
            resume_dir = os.path.join(directory,"Resumes")
            resume_uuid_name = str(uuid.uuid4().hex) + ".pdf"
            resume_path = os.path.join(resume_dir,resume_uuid_name)
            uploaded_file.save(resume_path)
            spacy_ner_detection.extract_resume_details(resume_path,resume_uuid_name)
        return redirect(url_for('upload_resume'))
    return render_template('upload.html')

def show_calendar_for_interview(chat_id):
    bot.send_message(chat_id=chat_id, text = "Please choose a date for your interview with the candidate.",reply_markup=telegramcalendar.create_calendar())

def show_time_slots_for_interview(chat_id):
    bot.send_message(chat_id=chat_id, text = "Please choose a time slot on the chosen date for your interview with the candidate.",reply_markup=telegramcalendar.create_time_selection())

if __name__ == "__main__":
    app.run(threaded=True)