import spacy
import warnings
from pymongo import MongoClient
from io import StringIO
import os
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
import re

nlp=spacy.load('resume_model')
jd_nlp = spacy.load('jd_model')
jd_exp_nlp = spacy.load('jd_exp_model')

myclient =  MongoClient("mongodb+srv://user:user@cluster0.oklqw.mongodb.net/test")
mydb = myclient["plp_project"]

def convert_pdf_to_txt(path):
    resource_manager = PDFResourceManager()
    device = None
    try:
        with StringIO() as string_writer, open(path, 'rb') as pdf_file:
            device = TextConverter(resource_manager, string_writer, codec='utf-8', laparams=LAParams(line_margin=1))
            interpreter = PDFPageInterpreter(resource_manager, device)

            for page in PDFPage.get_pages(pdf_file):
                interpreter.process_page(page)

            pdf_text = string_writer.getvalue()
    finally:
        if device:
            device.close()
    print(pdf_text)
    return pdf_text

def save_candidate(resume_info,file_name):
    schema = mydb["resume_details"]
    email = resume_info['Email']
    data = {"Name":resume_info['Name'][0], "Email": resume_info['Email'][0], "Status": "RESUME_UPLOADED", "Resume_Doc": file_name}
    myquery = {"Email": email}
    existing_user = list(schema.find(myquery))
    if (len(existing_user) == 0):
        schema.insert_one(data)


def extract_resume_details(path,resume_file_name):
    data = convert_pdf_to_txt(path)
    
    directory = os.getcwd()
    file_name = resume_file_name[:resume_file_name.find('.pdf')]
    print(file_name)
    f=open(os.path.join(directory,"ExtractedResumes/"+file_name+".txt"),"w")

    # Extracting Skills, Names, Experience etc from Resume
    doc_to_test=nlp(data)
    resume_dict={}
    for ent in doc_to_test.ents:
        resume_dict[ent.label_]=[]
    for ent in doc_to_test.ents:
        resume_dict[ent.label_].append(ent.text)

    save_candidate(resume_dict,file_name)
    for i in set(resume_dict.keys()):

        f.write("\n\n")
        f.write(i +":"+"\n")
        for j in set(resume_dict[i]):
            f.write(j.replace('\n','')+"\n")

def extract_jd_details(jd_file_path,job_id):
    text = convert_pdf_to_txt(jd_file_path)
    print(text)

    text = re.sub(r'(.)\1{3,}', r'\1', text)
    text = text.encode("ascii", "ignore").decode()
    doc = jd_nlp(text)
    
    skill = []
    degree = []
    title = []
    exp = []
    for ent in doc.ents:
        if ent.label_ == 'Skill':
            skill.append(ent.text)
        elif ent.label_ == 'Degree':
            degree.append(ent.text )
        elif ent.label_ == 'Title':
            title.append(ent.text)
        elif ent.label_ == 'Experience':
            exp.append(ent.text)
    
    if len(exp)<1:
        doc_exp = jd_exp_nlp(text)
        
        for ent in doc_exp.ents:
            exp.append(ent.text.encode("ascii", "ignore").decode())
    
    skill = [i.rstrip('/').lstrip('/').rstrip() for i in skill]
    skill = list(set(skill))
    result = {"degree": degree,
              "exp"   : exp,
              "title" : title,
              "skills": skill}
    
    directory = os.getcwd()
    f=open(os.path.join(directory,"ExtractedJobDescriptions/"+job_id+".txt"),"w")

    for i in set(result.keys()):
        f.write("\n\n")
        f.write(i +":"+"\n")
        for j in set(result[i]):
            f.write(j.replace('\n','')+"\n")
