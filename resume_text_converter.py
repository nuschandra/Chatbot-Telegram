import spacy
import warnings
from pymongo import MongoClient
import uuid
from io import StringIO

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
import os
import re

directory=os.getcwd()

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
    #text_file = os.path.join(directory,"TextResumes/Astha.txt")
    #f=open(text_file,"w")
    #pdf_text = pdf_text.replace(u"\xa0", u" ")
    #f.write(pdf_text)
    #f.close()
    return pdf_text

resume_dir=os.path.join(directory,"Resumes/Atri.pdf")
text_file = convert_pdf_to_txt(resume_dir)

'''blue_portion_titles=[' \n','Contact\n','Top Skills\n','Languages\n','Certifications\n','Honors-Awards\n','Publications\n','Patents\n']
check=True
with open(resume_dir) as f:
    for line in f:
        if(check):
            if(line in blue_portion_titles):
                check=False
                continue
            elif('www.linkedin' in line):
                check=False
                continue
            else:
                name=line.replace("\n","")
                print("The name is: " + name)
                break
        if(line=='\n'):
            check=True'''

regex = '\S+@\S+'
email = re.findall(regex, text_file) 
if(len(email)!=0):
    print(email[0])

regex = '(www.linkedin.com)+(.|\n|\r)*\(LinkedIn\)'
contact = re.search(regex, text_file)
if(contact!=None):
    contact=contact.group().replace("\n","")
    print(contact)
else:
    print("N/A")