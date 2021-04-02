from telegram import InlineKeyboardButton, InlineKeyboardMarkup,ReplyKeyboardRemove
import datetime
import calendar
import ast


def create_callback_data(type_of_callback,action,year,month,day,candidate_id,job_id):
    """ Create the callback data associated to each button"""
    callback_data=";".join([type_of_callback,action,str(year),str(month),str(day),candidate_id,job_id])
    return str(callback_data)

def create_time_callback_data(type_of_callback,action,time,interview_oid):
    """ Create the callback data associated to each button"""
    callback_data=";".join([type_of_callback,action,str(time),interview_oid])
    return str(callback_data)

def separate_callback_data(data):
    """ Separate the callback data"""
    return data.split(";")


def create_calendar(candidate_id,job_id,year=None,month=None):
    """
    Create an inline keyboard with the provided year and month
    :param int year: Year to use in the calendar, if None the current year is used.
    :param int month: Month to use in the calendar, if None the current month is used.
    :return: Returns the InlineKeyboardMarkup object with the calendar.
    """
    now = datetime.datetime.now()
    if year == None: year = now.year
    if month == None: month = now.month
    data_ignore = create_callback_data("D","IGNORE", year, month, 0, "","")
    keyboard = []
    #First row - Month and Year
    row=[]
    row.append(InlineKeyboardButton(calendar.month_name[month]+" "+str(year),callback_data=data_ignore))
    keyboard.append(row)
    #Second row - Week Days
    row=[]
    for day in ["Mo","Tu","We","Th","Fr","Sa","Su"]:
        row.append(InlineKeyboardButton(day,callback_data=data_ignore))
    keyboard.append(row)

    my_calendar = calendar.monthcalendar(year, month)
    for week in my_calendar:
        row=[]
        for day in week:
            if(day==0):
                row.append(InlineKeyboardButton(" ",callback_data=data_ignore))
            else:
                row.append(InlineKeyboardButton(str(day),callback_data=create_callback_data("D","D",year,month,day,candidate_id,job_id)))
        keyboard.append(row)
    #Last row - Buttons
    row=[]
    row.append(InlineKeyboardButton("<",callback_data=create_callback_data("D","P-M",year,month,day,candidate_id,job_id)))
    row.append(InlineKeyboardButton(" ",callback_data=data_ignore))
    row.append(InlineKeyboardButton(">",callback_data=create_callback_data("D","N-M",year,month,day,candidate_id,job_id)))
    keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)

def create_time_selection(interview_oid,time=None):
    data_ignore = create_time_callback_data("TIME","IGNORE", time, "")
    keyboard = []
    row=[]
    row.append(InlineKeyboardButton("Available Time Slots",callback_data=data_ignore))
    keyboard.append(row)

    row=[]
    for time in ["9:00","10:00","11:00","12:00","13:00"]:
        row.append(InlineKeyboardButton(time,callback_data=create_time_callback_data("TIME","TIME",str(time),interview_oid)))
    keyboard.append(row)

    row=[]
    for time in ["14:00","15:00","16:00","17:00","18:00"]:
        row.append(InlineKeyboardButton(time,callback_data=create_time_callback_data("TIME","TIME",str(time),interview_oid)))
    keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def process_calendar_selection(bot,update):
    """
    Process the callback_query. This method generates a new calendar if forward or
    backward is pressed. This method should be called inside a CallbackQueryHandler.
    :param telegram.Bot bot: The bot, as provided by the CallbackQueryHandler
    :param telegram.Update update: The update, as provided by the CallbackQueryHandler
    :return: Returns a tuple (Boolean,datetime.datetime), indicating if a date is selected
                and returning the date if so.
    """
    ret_data = (False,None,"","")
    query = update.callback_query
    context = update.callback_query.data
    (callback_type,action,year,month,day,candidate_id,job_id) = separate_callback_data(context)
    curr = datetime.datetime(int(year), int(month), 1)
    if action == "IGNORE":
        bot.answer_callback_query(callback_query_id= query.id)
    elif action == "D":
        bot.edit_message_text(text=query.message.text,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id)
        ret_data = True,datetime.datetime(int(year),int(month),int(day)),candidate_id,job_id
    elif action == "P-M":
        pre = curr - datetime.timedelta(days=1)
        bot.edit_message_text(text=query.message.text,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            reply_markup=create_calendar(candidate_id,job_id,int(pre.year),int(pre.month)))
    elif action == "N-M":
        ne = curr + datetime.timedelta(days=31)
        bot.edit_message_text(text=query.message.text,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            reply_markup=create_calendar(candidate_id,job_id,int(ne.year),int(ne.month)))
    else:
        bot.answer_callback_query(callback_query_id= query.id,text="Something went wrong!")
        # UNKNOWN
    return ret_data

def process_time_selection(bot,update):
    ret_data = (False,None,"")
    query = update.callback_query
    print(query)
    context = update.callback_query.data
    (callback_type,action,time,interview_oid) = separate_callback_data(context)
    if action == "IGNORE":
        bot.answer_callback_query(callback_query_id= query.id) 
    elif action == "TIME":
        bot.edit_message_text(text=query.message.text,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id)
        
        d = datetime.datetime.strptime(time, "%H:%M")
        selected_time = d.strftime("%I:%M%p")
        ret_data = True,selected_time, interview_oid
    else:
        bot.answer_callback_query(callback_query_id= query.id,text="Something went wrong!")
        # UNKNOWN
    return ret_data