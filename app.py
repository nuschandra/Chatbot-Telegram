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
import schedule
from threading import Thread
from time import sleep
from bson import ObjectId
import recommendation

app = Flask(__name__)

bot_token = "1621891888:AAHBvpvmFNJDQoDlpB3ImaBwdQHOGn5d0Pg"
bot_username = "VirtualRecruiterBot"
bot_url = "https://b9e5a020b8d7.ngrok.io/"
bot = telegram.Bot(token=bot_token)
bot.delete_webhook(drop_pending_updates=True)
bot_url =  "https://732fa7b2da05.ngrok.io/"
bot.setWebhook('{URL}{HOOK}'.format(URL=bot_url, HOOK=bot_token))


def get_schedule(bot,chat_id,sch_list):
    button_list = []
    for cn,objid,sch in sch_list:
        dic=";".join(["show_confirm",objid])
        button_list.append(InlineKeyboardButton("Name: "+cn+"\n"+sch,callback_data=str(dic)))
       
    button_list  = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    reply_markup=InlineKeyboardMarkup(button_list)
    bot.send_message(chat_id=chat_id, text='This is your schedule. Please click on the buttons below to confirm or cancel.',reply_markup=reply_markup)
    return

def show_confirm(bot, chat_id, obj_id, name, date, time,msg_id):
    yes = ";".join(["confirm",obj_id])
    no = ";".join(["cancel",obj_id])
    button_list = [
        InlineKeyboardButton('Cancel', callback_data=str(no)),
        InlineKeyboardButton('Confirm', callback_data=str(yes))
    ]
    button_list = [button_list[i:i + 2] for i in range(0, len(button_list), 2)]
    reply_markup = InlineKeyboardMarkup(button_list)
    text = 'Kindly click on the buttons to confirm or cancel your interview.\n\n' + "Name: "+name+"\n"+"Timing: "+date + ", " + time
    bot.edit_message_text(chat_id=chat_id, text=text,message_id=msg_id,
                     reply_markup=reply_markup)
    return

def update_performance(bot,chat_id,completed_interviews):
    if (len(completed_interviews)==0):
        bot.send_message(chat_id=chat_id, text='These are the interviews you have completed so far. Kindly click on the candidate name to update the performance.')
        return
    button_list = []
    for interview in completed_interviews:
        objid=interview['_id']
        candidate_id=str(interview['candidate_id'])
        name,email=database_updates.get_candidate_info(candidate_id)
        date = interview["interview_date"].strftime(
                                    '%B') + " " + interview["interview_date"].strftime('%d')
        time = interview["interview_time"]
        dic=";".join(["update_performance",str(objid)])
        button_list.append(InlineKeyboardButton("Name: "+name+"\n"+date + ", "+time,callback_data=str(dic)))
       
    button_list  = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    reply_markup=InlineKeyboardMarkup(button_list)
    bot.send_message(chat_id=chat_id, text='Kindly click on the candidate names to update the performance.',reply_markup=reply_markup)
    return

def select_reject_candidate(bot, chat_id, obj_id, name, date, time,msg_id):
    yes = ";".join(["hire",obj_id])
    no = ";".join(["hire_reject",obj_id])
    button_list = [
        InlineKeyboardButton('Reject', callback_data=str(no)),
        InlineKeyboardButton('Hire', callback_data=str(yes))
    ]
    button_list = [button_list[i:i + 2] for i in range(0, len(button_list), 2)]
    reply_markup = InlineKeyboardMarkup(button_list)
    text = 'Kindly click on the buttons below to reject or hire the candidate.\n\n' + "Name: "+name+"\n"+"Timing: "+date + ", " + time
    bot.edit_message_text(chat_id=chat_id, text=text,message_id=msg_id,
                     reply_markup=reply_markup)
    return

def handle_callback(bot,update):
    chat_id = update.callback_query.message.chat.id
    msg_id = update.callback_query.message.message_id
    
    context = update.callback_query.data
    print("Context is " + context)
    action = telegramcalendar.separate_callback_data(context)[0]
    print(action)
    if(action=='update_performance'):
        action,obj_id=telegramcalendar.separate_callback_data(context)
        name,date,time=database_updates.get_candidate_and_interview_info(obj_id)
        select_reject_candidate(bot,chat_id,obj_id,name,date,time,msg_id)
    if(action=='hire'):
        action,obj_id=telegramcalendar.separate_callback_data(context)
        if(database_updates.update_hiring_status(obj_id,"Candidate Hired")):
            bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text = "Thank you for the confirmation. We shall notify the candidate on the good news",reply_markup=None)
        else:
            bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text = "Sorry, you have already updated the performance of this candidate.",reply_markup=None)
    if(action=='hire_reject'):
        action,obj_id=telegramcalendar.separate_callback_data(context)
        if (database_updates.update_hiring_status(obj_id,"Candidate Rejected")):
            bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text = "Thank you for the confirmation. We shall notify the candidate that their application is unsuccessful.",reply_markup=None)
        else:
            bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text = "Sorry, you have already updated the performance of this candidate.",reply_markup=None)
    if(action=="show_confirm"):
        bot.editMessageReplyMarkup(chat_id=chat_id, message_id=msg_id, reply_markup=None)
        action,obj_id=telegramcalendar.separate_callback_data(context)
        name,date,time=database_updates.get_candidate_and_interview_info(obj_id)
        show_confirm(bot,chat_id,obj_id,name,date,time,msg_id)
    if(action=="confirm"):
        action,obj_id=telegramcalendar.separate_callback_data(context)
        name,date,time=database_updates.get_candidate_and_interview_info(obj_id)
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text = "Thank you for confirming the interview! The details are as below:\n\n" + "Name: "+name+"\n"+"Timing: "+date + ", " + time,reply_markup=None)
    elif(action=="delete_sce"):
        bot.editMessageReplyMarkup(chat_id=chat_id, message_id=msg_id, reply_markup=None)
        bot.send_message(chat_id=chat_id, text = "Confirmed the appointment!")
    elif(action=="cancel"):
        action,obj_id=telegramcalendar.separate_callback_data(context)
        database_updates.cancel_schedule(obj_id)
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text = "I have cancelled the interview with the candidate.", reply_markup=None)
    elif(action=="Accept"):
        action,candidate_id=telegramcalendar.separate_callback_data(context)
        bot.editMessageReplyMarkup(chat_id=chat_id, message_id=msg_id, reply_markup=None)
        date,time=telegram_message_processing.check_duplicate_interview(chat_id,candidate_id)
        if (date==None and time ==None):
            show_calendar_for_interview(chat_id,candidate_id)
        else:
            bot.send_message(chat_id=chat_id, text = "You already have an interview scheduled with this candidate on " + date + " at " + time)
    elif(action=="Reject"):
        action,candidate_id=telegramcalendar.separate_callback_data(context)
        bot.editMessageReplyMarkup(chat_id=chat_id, message_id=msg_id, reply_markup=None)
        bot.send_message(chat_id=chat_id, text = "Rejected candidate")
    elif(action=="DATE"): # D stands for Date
        selected,date,candidate_id=telegramcalendar.process_calendar_selection(bot,update)
        if selected:
            today = datetime.now().strftime("%d/%m/%Y")
            current_selected_date = date.strftime("%d/%m/%Y")
            if (current_selected_date<=today):
                bot.send_message(chat_id=update.callback_query.from_user.id,
                        text="The date you've selected is invalid. Please choose a valid date.",
                        reply_markup=None)
                show_calendar_for_interview(chat_id)
            else:
                bot.edit_message_text(chat_id=update.callback_query.from_user.id,message_id=msg_id,
                        text="You selected %s" % current_selected_date,
                        reply_markup=None)
                if(candidate_id!=""):
                    database_updates.save_interview_date(date,candidate_id,chat_id,"interview_scheduled")
                    show_time_slots_for_interview(chat_id,candidate_id)
    elif(action=="TIME"): # T stands for time
        selected,time,candidate_id=telegramcalendar.process_time_selection(bot,update)
        if selected:
            bot.edit_message_text(chat_id=update.callback_query.from_user.id,message_id=msg_id,
                        text="Your interview has been scheduled at %s" % time,
                        reply_markup=None)
            database_updates.save_interview_time(time,candidate_id,chat_id)

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
        
            if intent == 'schedule_list' and type(response) != str:
                # if text == 'schedule_list':
                # sch_list = [("Candidate Name1","602a22d7829ac6fe97dc7b93","May 12, 4pm"),
                #             ("Candidate Name2","602a2332829ac6fe97dc7b95","Dec 2, 5pm"),
                #             ("Candidate Name3","602a2af515fb6f9e7a3e7d6f","Mar 12, 2pm")]

                get_schedule(bot, chat_id, response)
                return

            if intent == 'update_performance' and type(response)!=str:
                update_performance(bot,chat_id,response)
                return

            bot.sendMessage(chat_id=chat_id, text=response, reply_to_message_id=msg_id) 
            
    elif update['message']['document'] != None:
        file_type = update.message.document.mime_type
        print("File type is:" + file_type)
        if(database_updates.check_user_status(chat_id)):
        # if (True):
            if file_type != 'text/plain':
                error_message = "Sorry, kindly make sure you upload a txt file only."
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
                    candidate_id=info['id']
                    file_to_send = "Resumes/"+str(ids)+".pdf"
                    #get_candidate_details = database_updates.hire_request(ids)
                    get_candidate_details = "Name: "+name+"\n"+"Email: "+email
                    accept=";".join(["Accept",candidate_id])
                    reject=";".join(["Reject",candidate_id]) 
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
    error=None
    if request.method == 'POST':
        uploaded_file = request.files['file']
        if uploaded_file.filename != '':
            directory = os.getcwd()
            resume_dir = os.path.join(directory,"Resumes")
            resume_uuid_name = str(uuid.uuid4().hex) + ".pdf"
            resume_path = os.path.join(resume_dir,resume_uuid_name)
            uploaded_file.save(resume_path)
            #spacy_ner_detection.extract_resume_details(resume_path,resume_uuid_name)
            try:
                recommendation.populate_resume(resume_path)
            except Exception as e:
                if(str(e)=="The resume is already present in our system."):
                    error="The resume is already present in our system."
                    return render_template('upload.html',error=error)
        return redirect(url_for('upload_resume'))
    return render_template('upload.html',error=error)

def show_calendar_for_interview(chat_id,can_id):
    bot.send_message(chat_id=chat_id, text = "Please choose a date for your interview with the candidate.",reply_markup=telegramcalendar.create_calendar(can_id))

def show_time_slots_for_interview(chat_id,can_id):
    bot.send_message(chat_id=chat_id, text = "Please choose a time slot on the chosen date for your interview with the candidate.",reply_markup=telegramcalendar.create_time_selection(can_id))

def schedule_checker():
    while True:
        schedule.run_pending()
        sleep(1)

def send_reminder():
    print("Scheduler running now")
    scheduled_interviews = database_updates.find_interviews_scheduled_for_the_day()
    for interview in scheduled_interviews:
        chat_id=interview['manager_id']
        name,email=database_updates.get_candidate_info(interview['candidate_id'])
        text="This is to remind you that you have an interview scheduled today. The interview details are: \n\n" + "Name: " + name + "\nTime: " + interview['interview_time']
        bot.send_message(chat_id=chat_id,text=text)

schedule.every().day.at("08:00").do(send_reminder)
Thread(target=schedule_checker).start()

if __name__ == "__main__":

    app.run(threaded=True)