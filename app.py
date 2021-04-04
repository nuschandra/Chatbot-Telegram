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
from flask_mail import Mail, Message
from flask import current_app

app = Flask(__name__)
mail=Mail(app)

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT']=465
app.config['MAIL_USERNAME']='wayne.enterprises.plp@gmail.com'
app.config['MAIL_PASSWORD']='wayne@123'
app.config['MAIL_USE_TLS']=False
app.config['MAIL_USE_SSL']=True
mail=Mail(app)

bot_token = "1621891888:AAHBvpvmFNJDQoDlpB3ImaBwdQHOGn5d0Pg"
bot_username = "VirtualRecruiterBot"
bot_url = "https://b9e5a020b8d7.ngrok.io/"
bot = telegram.Bot(token=bot_token)
bot.delete_webhook(drop_pending_updates=True)
bot_url =  "https://fb4ce1181e60.ngrok.io/"
bot.setWebhook('{URL}{HOOK}'.format(URL=bot_url, HOOK=bot_token))


def get_schedule(bot,chat_id,sch_list):
    button_list = []
    for cn,objid,sch in sch_list:
        dic=";".join(["show_confirm",objid])
        button_list.append(InlineKeyboardButton(cn+"\n"+sch,callback_data=str(dic)))
       
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
    bot.send_message(chat_id=chat_id, text=text,
                     reply_markup=reply_markup)
    return

def update_performance(bot,chat_id,completed_interviews):
    if (len(completed_interviews)==0):
        bot.send_message(chat_id=chat_id, text='You have no interviews to update at the moment.')
        return
    button_list = []
    for interview in completed_interviews:
        objid=interview['_id']
        candidate_id=str(interview['candidate_id'])
        name,email=database_updates.get_candidate_info(candidate_id)
        date = interview["interview_date"].strftime(
                                    '%B') + " " + interview["interview_date"].strftime('%d')
        time = interview["interview_time"]
        title=interview['job_title']
        dic=";".join(["update_performance",str(objid)])
        button_list.append(InlineKeyboardButton("Name: "+name+"\n"+date + ", "+time +"\n"+"Title: "+title,callback_data=str(dic)))
       
    button_list  = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    reply_markup=InlineKeyboardMarkup(button_list)
    bot.send_message(chat_id=chat_id, text='Kindly click on the candidate names to update the performance.',reply_markup=reply_markup)
    return

def select_reject_candidate(bot, chat_id, obj_id, name, date, time,msg_id,title):
    yes = ";".join(["hire",obj_id])
    no = ";".join(["hire_reject",obj_id])
    button_list = [
        InlineKeyboardButton('Reject', callback_data=str(no)),
        InlineKeyboardButton('Hire', callback_data=str(yes))
    ]
    button_list = [button_list[i:i + 2] for i in range(0, len(button_list), 2)]
    reply_markup = InlineKeyboardMarkup(button_list)
    text = 'Kindly click on the buttons below to reject or hire the candidate.\n\n' + "Name: "+name+"\n"+"Timing: "+date + ", " + time + "\n"+"Title: "+title
    bot.send_message(chat_id=chat_id, text=text,
                     reply_markup=reply_markup)
    return

def close_job_opening(chat_id,job_id,job_title):
    close = ";".join(["close",job_id])
    open_job = ";".join(["open",job_id])
    button_list = [
        InlineKeyboardButton('Close', callback_data=str(close)),
        InlineKeyboardButton('Keep it open', callback_data=str(open_job))
    ]
    button_list = [button_list[i:i + 2] for i in range(0, len(button_list), 2)]
    reply_markup = InlineKeyboardMarkup(button_list)
    close_job_text="Since you have hired a candidate, would you like to close the " + job_title + " opening? You can keep it open if you would like to hire more candidates for this role."
    bot.send_message(chat_id=chat_id, text=close_job_text,reply_markup=reply_markup)
    return

def handle_callback(bot,update):
    chat_id = update.callback_query.message.chat.id
    msg_id = update.callback_query.message.message_id
    
    context = update.callback_query.data
    print("Context is " + context)
    action = telegramcalendar.separate_callback_data(context)[0]
    print(action)
    if(action=='close'):
        action,job_id=telegramcalendar.separate_callback_data(context)
        database_updates.close_job(job_id)
        database_updates.reject_pending_candidates(job_id,chat_id)
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text = "Thank you for the confirmation. We have closed this job opening.",reply_markup=None)
    if(action=='open'):
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text = "Thank you for the confirmation.",reply_markup=None)
    if(action=='update_performance'):
        action,obj_id=telegramcalendar.separate_callback_data(context)
        name,date,time,title,can_id=database_updates.get_candidate_and_interview_info(obj_id)
        select_reject_candidate(bot,chat_id,obj_id,name,date,time,msg_id,title)
    if(action=='hire'):
        action,obj_id=telegramcalendar.separate_callback_data(context)
        job_id,job_title = database_updates.get_job_info_from_interview_obj_id(obj_id)
        name,db_date,db_time,title,can_id=database_updates.get_candidate_and_interview_info(obj_id)

        if(database_updates.update_hiring_status(obj_id,"Candidate Hired")):
            bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text = "Thank you for the confirmation. We shall notify the candidate on the good news",reply_markup=None)
            text="Hi "+name+",\n\nCongratulations! We are happy to inform you that you have been selected for the role of " + job_title +". We will keep you informed on more details shortly.\n\nRegards,\nWayne Enterprises"
            email_candidate_template("CONGRATULATIONS!",text)
            close_job_opening(chat_id,job_id,job_title)
        else:
            bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text = "Sorry, you have already updated the performance of this candidate.",reply_markup=None)
    if(action=='hire_reject'):
        action,obj_id=telegramcalendar.separate_callback_data(context)
        job_id,job_title = database_updates.get_job_info_from_interview_obj_id(obj_id)
        name,db_date,db_time,title,can_id=database_updates.get_candidate_and_interview_info(obj_id)
        if (database_updates.update_hiring_status(obj_id,"Candidate Rejected")):
            bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text = "Thank you for the confirmation. We shall notify the candidate that their application is unsuccessful.",reply_markup=None)
            text="Hi "+name+",\n\nWe are sorry to inform you that you have not been selected for the role of " + job_title +". We will keep your resume on file and will let you know if you are shortlisted for any other roles.\n\nRegards,\nWayne Enterprises"
            email_candidate_template("Update from Wayne Enterprises",text)
        else:
            bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text = "Sorry, you have already updated the performance of this candidate.",reply_markup=None)
    if(action=="show_confirm"):
        action,obj_id=telegramcalendar.separate_callback_data(context)
        try:
            name,date,time,title,can_id=database_updates.get_candidate_and_interview_info(obj_id)
        except Exception as e:
            bot.send_message(chat_id=chat_id, text=str(e))
            return
        show_confirm(bot,chat_id,obj_id,name,date,time,msg_id)
    if(action=="confirm"):
        action,obj_id=telegramcalendar.separate_callback_data(context)
        name,date,time,title,can_id=database_updates.get_candidate_and_interview_info(obj_id)
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id,text = "Thank you for confirming the interview! The details are as below:\n\n" + "Name: "+name+"\n"+"Timing: "+date + ", " + time,reply_markup=None)
    elif(action=="delete_sce"):
        bot.editMessageReplyMarkup(chat_id=chat_id, message_id=msg_id, reply_markup=None)
        bot.send_message(chat_id=chat_id, text = "Confirmed the appointment!")
    elif(action=="cancel"):
        action,obj_id=telegramcalendar.separate_callback_data(context)
        job_id,job_title=database_updates.get_job_info_from_interview_obj_id(obj_id)
        name,db_date,db_time,title,can_id=database_updates.get_candidate_and_interview_info(obj_id)
        database_updates.cancel_schedule(obj_id)
        text="I have cancelled the interview with the candidate. Kindly reschedule the interview to another date and time."
        bot.delete_message(chat_id,msg_id)
        email_text="Hi " + name +",\n\nWe are sorry to inform you that your interview on " + db_date + " at " + db_time + " has been cancelled due to unforeseen circumstances. You will receive another email shortly with the new timing.\n\nRegards,\nWayne Enterprises"
        email_candidate_template("Interview Cancelled",email_text)

        show_calendar_for_interview(text,chat_id,can_id,job_id)

    elif(action=="Accept"):
        action,candidate_id,job_id=telegramcalendar.separate_callback_data(context)
        job_title=database_updates.get_job_title_based_on_jobid(job_id)
        bot.editMessageReplyMarkup(chat_id=chat_id, message_id=msg_id, reply_markup=None)
        date,time,status=telegram_message_processing.check_duplicate_interview(chat_id,candidate_id,job_title)
        if (date==None and time==None and status==None):
            text='Please choose a date for your interview with the candidate.'
            show_calendar_for_interview(text,chat_id,candidate_id,job_id)
        else:
            if(status=='interview_scheduled'):
                bot.send_message(chat_id=chat_id, text = "You already have an interview scheduled with this candidate on " + date + " at " + time + " for the " + job_title + " role.")
            elif(status=='Candidate Hired'):
                bot.send_message(chat_id=chat_id, text = "You have already hired this candidate for the " + job_title + " role.")
            elif(status=='Candidate Rejected'):
                bot.send_message(chat_id=chat_id, text = "You have already rejected this candidate for the " + job_title + " role.")

    elif(action=="Reject"):
        action,candidate_id,job_id=telegramcalendar.separate_callback_data(context)
        name,email=database_updates.get_candidate_info(candidate_id)
        database_updates.save_interview_date("N/A",candidate_id,chat_id,job_id,"Candidate Rejected")
        bot.editMessageReplyMarkup(chat_id=chat_id, message_id=msg_id, reply_markup=None)
        bot.send_message(chat_id=chat_id, text = "We have noted that you are rejecting " + name + " for this job role.")
    elif(action=="D"): # D stands for Date
        selected,date,candidate_id,job_id=telegramcalendar.process_calendar_selection(bot,update)
        if selected:
            today = datetime.now()
            if (date<=today):
                text='The date you have selected is either in the past or too late to schedule. Please choose a valid date.'
                show_calendar_for_interview(text,chat_id,candidate_id,job_id)
            else:
                #bot.edit_message_text(chat_id=update.callback_query.from_user.id,message_id=msg_id,
                #        text="You selected %s" % current_selected_date,
                #        reply_markup=None)
                if(candidate_id!=""):
                    interview_oid = database_updates.save_interview_date(date,candidate_id,chat_id,job_id,"interview_scheduled")
                    show_time_slots_for_interview(chat_id,interview_oid,msg_id)
    elif(action=="TIME"): # T stands for time
        selected,time,interview_oid=telegramcalendar.process_time_selection(bot,update)
        if selected:
            name,db_date,db_time,title,can_id=database_updates.get_candidate_and_interview_info(interview_oid)
            if (telegram_message_processing.check_candidate_availability(db_date,time,can_id)):
                if(telegram_message_processing.check_manager_availability(db_date,time,chat_id)):
                    database_updates.save_interview_time(time,interview_oid)
                    bot.edit_message_text(chat_id=update.callback_query.from_user.id,message_id=msg_id,
                        text="Your interview has been scheduled at " + time + " on "  + db_date + " with " + name + " for the " + title + " role.",
                        reply_markup=None)
                    text="Hi " + name + ",\n\nWe are happy to let you know that an interview has been scheduled on " +db_date+ " at " + time + " for the " + title + " role.\n\nRegards,\nWayne Enterprises"
                    email_candidate_template("Interview Scheduled",text)
                else:
                    job_id,job_title=database_updates.get_job_info_from_interview_obj_id(interview_oid)
                    database_updates.cancel_schedule(interview_oid)
                    bot.delete_message(chat_id,msg_id)
                    response = "You have scheduled another interview on the given date and time. Therefore, kindly choose another date and time for your interview."
                    show_calendar_for_interview(response,chat_id,can_id,job_id)

            else:
                job_id,job_title=database_updates.get_job_info_from_interview_obj_id(interview_oid)
                database_updates.cancel_schedule(interview_oid)
                bot.delete_message(chat_id=chat_id,message_id=msg_id)
                response = "The candidate has another interview on the given date and time. Therefore, kindly choose another date and time for your interview."
                show_calendar_for_interview(response,chat_id,can_id,job_id)

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
                jd_file,job_id = telegram_message_processing.process_file(file_id,bot_token)
                try:
                    telegram_message_processing.save_jd_in_database(jd_file,job_id,chat_id)
                except Exception as e:
                    os.remove(jd_file)
                    bot.sendMessage(chat_id=chat_id, text=str(e), reply_to_message_id=msg_id)
                    return

                response = "Thank you for uploading the job description. Our algorithm will identify and recommend the best suited candidates to you."
                bot.sendMessage(chat_id=chat_id, text=response, reply_to_message_id=msg_id)
                if(not os.path.isfile("resume_details.csv")):
                    response = "Sorry! We did not find any resume matching your requirements. We will notify if we find anything in the future."
                    bot.sendMessage(chat_id=chat_id, text=response)
                    return

                resume_info = telegram_message_processing.trigger_resume_fetching(jd_file,job_id,chat_id)
                if (len(resume_info)==0):
                    response = "Sorry! We did not find any resume matching your requirements. We will notify if we find anything in the future."
                    bot.sendMessage(chat_id=chat_id, text=response)
                    return
                    
                for info in resume_info:
                    ids=info['resume_doc']
                    name=info['name']
                    email=info['email']
                    candidate_id=info['id']
                    degree=info['degree']
                    file_to_send = os.path.join(os.getcwd(),"Resumes/"+str(ids)+".pdf")
                    #get_candidate_details = database_updates.hire_request(ids)
                    get_candidate_details = "Name: "+name+"\n"
                    if email!='N/A':
                        get_candidate_details = get_candidate_details + "Email: " + email+"\n"
                    get_candidate_details=get_candidate_details+"Degree: " + degree
                    accept=";".join(["Accept",candidate_id,job_id])
                    reject=";".join(["Reject",candidate_id,job_id]) 
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
    flag=False
    if request.method == 'POST':
        uploaded_file = request.files['file']
        if(request.form.get('want-daily-emails')):
            flag=True

        if uploaded_file.filename != '':
            directory = os.getcwd()
            resume_dir = os.path.join(directory,"Resumes")
            resume_uuid_name = str(uuid.uuid4().hex) + ".pdf"
            resume_path = os.path.join(resume_dir,resume_uuid_name)
            uploaded_file.save(resume_path)
            #spacy_ner_detection.extract_resume_details(resume_path,resume_uuid_name)
            try:
                name,email,linkedin_contact=recommendation.save_resume_in_db(resume_path,flag)
            except Exception as e:
                os.remove(resume_path)
                if(str(e)=="The resume is already present in our system."):
                    error="The resume is already present in our system."
                    return render_template('upload.html',error=error)
            
            send_email_to_candidate(name,flag)
            resume_matched_list=recommendation.new_resumes_recommendation(resume_path,name)
            if(len(resume_matched_list)>0):
                send_resumes_to_managers(resume_matched_list,resume_path)
        return redirect(url_for('upload_resume'))
    return render_template('upload.html',error=error)

def send_email_to_candidate(name,flag):
    msg=Message('Acknowledging resume submission',sender='wayne.enterprises.plp@gmail.com',recipients=['lakshmi.4296@gmail.com'])
    body = "Hi " + name + ",\n\n" + "We would like to acknowledge that we have received your resume. We will now match your resume against any job openings that maybe created by our hiring managers in the future. If your resume is deemed successful, we will certaintly reach out to you for further action.\n\n"
    if(flag):
        body_flag = "We also note that you would like to receive weekly updates on the status of your application."
    else:
        body_flag = "We also note that you would not like to receive weekly updates on the status of your application."
    body_close = "\n\nRegards,\nWayne Enterprises"
    msg.body=body + body_flag+body_close
    mail.send(msg)
    return "Sent"

def send_resumes_to_managers(resume_matched_list,resume_path):
    resume_file_name=resume_path[-36:-4]
    name,email,candidate_id=database_updates.get_candidate_name_email_id(resume_file_name)
    file_to_send = os.path.join(os.getcwd(),"Resumes/"+str(resume_file_name)+".pdf")
    #get_candidate_details = database_updates.hire_request(ids)


    for resume in resume_matched_list:
        job_id=resume['job_id']
        job_title=resume['job_title']
        chat_id=resume['manager_id']
        accept=";".join(["Accept",candidate_id,job_id])
        reject=";".join(["Reject",candidate_id,job_id]) 
        keyboard = [[InlineKeyboardButton("Accept", callback_data=str(accept))],
                    [InlineKeyboardButton("Reject", callback_data=str(reject))]]  

        get_candidate_details = "Name: "+name+"\n"
        if email!='N/A':
            get_candidate_details=get_candidate_details+"Email: "+email + "\n"
        get_candidate_details=get_candidate_details+"Degree: "+resume['degree']
        caption="We recently found a resume that may match the requirements you have indicated for the role of " + job_title + ".\n\n"  
        bot.sendDocument(chat_id=chat_id,document=open(file_to_send, 'rb'),caption=caption+get_candidate_details,reply_markup=InlineKeyboardMarkup(keyboard),filename=name+".pdf")
    return

def email_candidate_template(subject,text):
    msg=Message(subject,sender='wayne.enterprises.plp@gmail.com',recipients=['lakshmi.4296@gmail.com'])
    msg.body=text
    mail.send(msg)
    return

def show_calendar_for_interview(text,chat_id,can_id,job_id):
    bot.send_message(chat_id=chat_id, text = text,reply_markup=telegramcalendar.create_calendar(can_id,job_id))

def show_time_slots_for_interview(chat_id,interview_oid,msg_id):
    bot.edit_message_text(chat_id=chat_id,message_id=msg_id,text = "Please choose a time slot on the chosen date for your interview with the candidate.",reply_markup=telegramcalendar.create_time_selection(interview_oid))

def schedule_checker(app):
    with app.app_context():
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

def email_blast_to_candidates():
    print("Scheduler running now")
    candidates_in_db = database_updates.get_all_candidates()
    for candidate in candidates_in_db:
        candidate_id=candidate['_id']
        candidate_name=candidate['Name']
        if(database_updates.check_if_candidate_in_interview_details_table(candidate_id)):
            continue
        else:
            msg=Message('Update from Wayne Enterprises',sender='wayne.enterprises.plp@gmail.com',recipients=['lakshmi.4296@gmail.com'])
            msg.body="Hi "+candidate_name+",\n\n"+ "We are sorry to inform that we have still not found a job match for you. We will keep you posted in case there are any updates.\n\nRegards,\nWayne Enterprises"
            mail.send(msg)

def update_performance_reminder(bot,chat_id,completed_interviews):
    if (len(completed_interviews)==0):
        return
    button_list = []
    for interview in completed_interviews:
        objid=interview['_id']
        candidate_id=str(interview['candidate_id'])
        name,email=database_updates.get_candidate_info(candidate_id)
        date = interview["interview_date"].strftime(
                                    '%B') + " " + interview["interview_date"].strftime('%d')
        time = interview["interview_time"]
        title=interview['job_title']
        dic=";".join(["update_performance",str(objid)])
        button_list.append(InlineKeyboardButton("Name: "+name+"\n"+date + ", "+time +"\n"+"Title: "+title,callback_data=str(dic)))
       
    button_list  = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    reply_markup=InlineKeyboardMarkup(button_list)
    bot.send_message(chat_id=chat_id, text='This is to remind you that you are yet to update performance of the following candidates. Kindly click on the candidate names to update the performance.',reply_markup=reply_markup)
    return

def send_update_performance_reminder():
    print("Scheduler running now")
    managers_in_db=database_updates.get_all_managers()
    for manager in managers_in_db:
        completed_interviews=database_updates.find_completed_interviews(manager['chat_id'])
        update_performance_reminder(bot,manager['chat_id'],completed_interviews)

schedule.every().day.at("08:00").do(send_reminder)
schedule.every().day.at("09:00").do(send_update_performance_reminder)
schedule.every().monday.at("10:00").do(email_blast_to_candidates)
Thread(target=schedule_checker,args=[app]).start()

if __name__ == "__main__":

    app.run(threaded=True)