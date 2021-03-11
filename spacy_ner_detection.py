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

myclient =  MongoClient("mongodb+srv://user:user@cluster0.oklqw.mongodb.net/test")
mydb = myclient["plp_project"]

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