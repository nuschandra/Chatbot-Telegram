import spacy
import os
import re
from io import StringIO
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
import pandas as pd
from collections import defaultdict 
from nltk.corpus import stopwords
import numpy as np
from nltk import word_tokenize, pos_tag
import nltk
from nltk import ngrams
from word2number import w2n
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer 
from sklearn.metrics.pairwise import cosine_similarity
import database_updates
import spacy_ner_detection
import json

nlp_model = spacy.load('jd_model')
nlp_exp_model = spacy.load('jd_exp_model')
mystopwords=stopwords.words("English") + ['experience','computer,','science','expert','knowledge','plus','proficiency','understanding','excellent','ability','skill','responsibility']

nlp=spacy.load('resume_model3')
#nlp_experience = spacy.load('resume_model')
#nlp_degree = spacy.load('resume_model5')

lookup_dict = {'javascript' : ['js','javascript','jscript','java script'],
'nodejs' : ['node.js','node','nodejs','node js'],
'angularjs' : ['angularjs','angular.js','angular','angular js'],
'reactjs' : ['reactjs','react.js','react','react js'],
'vuejs' : ['vue.js','vue','vuejs','vue js'],
'artificial intelligence' : ['ai','artificial intelligence'],
'machine learning' : ['ml','machine learning'],
'deep learning' : ['dl','deep learning'],
'ms sql' : ['microsoft sql','ms sql','mssql'],
'sql' : ['sql','structured query language'],
'database' : ['database','db','databases']}

grammar = r"""
    NP1: {<CD><NN|NNS>}
    NP2: {<NN><CD>}
    NP3: {<CD><CC><JJR><NN|NNS>}
    NP4: {<CD>}
    NP5: {<JJ><NNS>}
    """
cp = nltk.RegexpParser(grammar)

with open('academic_degree.json') as json_file:
    degree_lookup = json.load(json_file)


def degree_flag(resume_degree, jd_degree):
    if jd_degree == []:
        return 'Qualified'
    degree = ['associate','diploma','bachelor','master','doctor','phd']
    jd_deg = []
    for i in degree:
        for k in  word_tokenize(" ".join(jd_degree).replace('.','').replace('\'',' ').lower()):
            if i in k:
                jd_deg.append(i)
    if jd_deg==[]:
        return 'Qualified'
    resume_deg = ''        
    for i in degree_lookup.keys():
        for j in degree_lookup[i]:
            if j.lower() in resume_degree.replace('.','').replace('\'',' ').lower():
                resume_deg = i
    if resume_deg != '':
        print(jd_deg,resume_deg)
        if degree.index(jd_deg[0]) < degree.index(resume_deg):
            return 'Over Qualified'
        elif degree.index(jd_deg[0]) > degree.index(resume_deg):
            return 'Not Qualified'
        else:
            print('Qualified',jd_deg,resume_deg)
            return 'Qualified'
    else:
        return 'NA'

def co_occ_matrix(sentences):
    print("Calculating co-occurence matrix")
    if os.path.isfile('co_occ_dict.pkl'):
        d = pickle.load(open('co_occ_dict.pkl','rb'))
    else:
        d = defaultdict(int)
        
    for text in sentences:
       text = text.lower().split()

       for i in range(len(text)):
           token = text[i]
           next_token = text[i+1 : i+1+2000]
           for t in next_token:
               key = tuple( sorted([t, token]) )
               d[key] += 1
               
    pickle.dump(d, open("co_occ_dict.pkl", "wb"))  
    vocab = set()
    for key, value in d.items():
        vocab.add(key[0])
        vocab.add(key[1])
        
    vocab = sorted(vocab)
    df = pd.DataFrame(data=np.zeros((len(vocab), len(vocab)), dtype=np.int16),
                  index=vocab,
                  columns=vocab)
    for key, value in d.items():
        df.at[key[0], key[1]] = value
        df.at[key[1], key[0]] = value
    return df


def extract_jd_details(jd_path):
    print("Hehe! Extracting JD details")
    f=open(jd_path,'r', encoding='utf-8')
    text = ""
    for x in f:
        text = text + x
    text = re.sub(r'(.)\1{3,}', r'\1', text)
    text = text.encode("ascii", "ignore").decode()
    doc = nlp_model(text)
    
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
        doc_exp = nlp_exp_model(text)
        
        for ent in doc_exp.ents:
            exp.append(ent.text.encode("ascii", "ignore").decode())
            
    skill = [i.rstrip('/').lstrip('/').rstrip() for i in skill]
    skill = list(set(skill))
    result = {"Degree": degree,
              "Exp"   : exp,
              "Title" : title,
              "Skill": skill}

    directory = os.getcwd()
    job_id=jd_path[-20:-4]
    f=open(os.path.join(directory,"ExtractedJobDescriptions/"+job_id+".txt"),"w")

    for i in set(result.keys()):
        f.write("\n\n")
        f.write(i +":"+"\n")
        for j in set(result[i]):
            f.write(j.replace('\n','')+"\n")
    return(result)

def look_up_skill(skills):
    for i in skills:
        for key in lookup_dict:
            if i.lower() in lookup_dict[key]:
                skills[skills.index(i)] = key
    return list(set(skills))
	
def join_grams(joinlist):	
    ret = []	
    for i in joinlist:	
        n=1	
        while(n<=len(i.split(' '))):	
            for gram in ngrams(i.split(), n): 	
                ret.append(''.join(gram).lower())	
            n+=1	
    return ' '.join(list(set(ret)))

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
    # print(pdf_text)
    return pdf_text

def extract_resume_details(path,names,titles,skills,filenames,degree,name):
    data = convert_pdf_to_txt(path)

    directory = os.getcwd()
    file_name = path[-36:-4]

    # Extracting Skills from Resume
    doc_to_test=nlp(data)

    # Extracting exp from Resume
    #doc_exp=nlp_experience(data)

    # Extracting degree from Resume
    #doc_degree=nlp_degree(data)
    resume_dict={}
    
    #resume_exp={}
    #resume_degree={}

    for ent in doc_to_test.ents:
        resume_dict[ent.label_]=[]
    for ent in doc_to_test.ents:
        resume_dict[ent.label_].append(ent.text)
    
    '''for ent in doc_exp.ents:
        resume_exp[ent.label_]=[]
    for ent in doc_exp.ents:
        resume_exp[ent.label_].append(ent.text)
    
    for ent in doc_degree.ents:
        resume_degree[ent.label_]=[]
    for ent in doc_degree.ents:
        resume_degree[ent.label_].append(ent.text)'''
    
    f=open(os.path.join(directory,"ExtractedResumes/"+file_name+".txt"),"w")

    for i in set(resume_dict.keys()):

        f.write("\n\n")
        f.write(i +":"+"\n")
        for j in set(resume_dict[i]):
            f.write(j.replace('\n','')+"\n")
    
    '''for i in set(resume_exp.keys()):
        f.write("\n\n")
        if (i=="Experience"):
            f.write(i +":"+"\n")
            for j in set(resume_exp[i]):
                f.write(j.replace('\n','')+"\n")
    for i in set(resume_degree.keys()):
        f.write("\n\n")
        if (i=="Degree"):
            f.write(i +":"+"\n")
            for j in set(resume_degree[i]):
                f.write(j.replace('\n','')+"\n")'''
    
    # for i in set(resume_dict.keys()):
        # print(resume_dict)
    li=[]
    extracted_degree=[]
    if 'Skills' in resume_dict.keys():
        for j in set(resume_dict['Skills']):
            li.append(j.replace('\n',''))
    if 'Degree' in resume_dict.keys():
        extracted_degree=resume_dict['Degree']
    if 'Experience' in resume_dict.keys():
        for j in set(resume_dict['Experience']):
            titles.append(j.replace('\n',''))
            skills.append(li)
            filenames.append(path)
            names.append(name)
            degree.append(' '.join(extracted_degree))
    else:
        skills.append(li)
        filenames.append(path)
        names.append(name)
        degree.append(' '.join(extracted_degree))
        titles.append('')

    return names,titles,skills,filenames,degree

def extract_name_email_linkedin(path,want_email_flag):
    data = convert_pdf_to_txt(path)

    directory = os.getcwd()
    file_name = path[-36:-4]
    text_file = os.path.join(directory,"TextResumes/"+file_name+".txt")
    f=open(text_file,"w")
    details_data = data.replace(u"\xa0", u" ")
    f.write(details_data)
    f.close()

    name=str(spacy_ner_detection.extract_name_rule(text_file))
    email=str(spacy_ner_detection.extract_email_rule(details_data))
    linkedin_contact=str(spacy_ner_detection.extract_linkedin_contact_rule(details_data))
    
    if(not database_updates.save_candidate(name,email,linkedin_contact,file_name,want_email_flag)):
        raise Exception("The resume is already present in our system.")

    return name,email,linkedin_contact

def extract_months(text):
    try:
        # m = re.search("[(]{1}[0-9]{0,2}[ a-zA-Z]{0,7}[0-9]{0,2}[a-zA-Z ]{0,7}[)]{1}", text)
        
        text = [i for i in re.findall('\[[^\]]*\]|\([^\)]*\)|\"[^\"]*\"|\S+',text) if 'year' in i or 'month' in i][0]
        # print(text)
        text = text.replace('(','').replace(')','')
        months = 0
        years = 0
        values = text.split(' ')
        if 'year' in text:
            years = values[0]
            if 'month' in text:
                 months = values[2]
        elif 'month' in text:
             months = values[0]
        else:
            return 0
        return 12*int(years) + int(months)
        
    except:
        return 0


def similar_doc(df,data,topn):
    print("I am going to calculate tf-idf")
    skill_match = df[['skills1','filename']].copy()
    skill_match = skill_match.drop_duplicates().copy()
    #skill_match['degree'] = skill_match['degree'].apply(lambda x : x.lower().replace(',','').replace('\'',''))
    #skill_match['train'] = skill_match['skills1']

    train = [' '.join([j if j in i.split() else 'dummy' for j in data.split() ]) for i in skill_match['skills1'].tolist()]

    tfidfvectoriser=TfidfVectorizer()
    tfidfvectoriser.fit(train)
    tfidf_vectors=tfidfvectoriser.transform(train)
    
    test_vec = tfidfvectoriser.transform([data])
    pairwise_similarities = np.dot([tfidf_vectors],[test_vec.T]).toarray().reshape((-1,))
    # pairwise_similarities = cosine_similarity(tfidf_vectors,test_vec).reshape((-1,))
    # print(pairwise_similarities)
    indices = np.nonzero(pairwise_similarities)[0]
    
    filenames = []
    for i in indices[np.argsort(pairwise_similarities[indices])][-topn:][::-1]:
        # print(skill_match.iloc[i]["skills1"])
        filenames.append(skill_match.iloc[i]["filename"])
    return filenames


def similar_exp(rec_skill,jd_exp,threshold,jd_title,df,co_occurrence_matrix):
    print("Experience based matching")
    rec_exp = []
    for i in rec_skill:
        exp = 0
        for j in df[df['filename'] == i]['title1'].tolist():
            # print(np.dot(co_occurrence_matrix[jd_title.lower().lstrip().rstrip().replace(' ','_')].tolist(),co_occurrence_matrix[j].T.tolist()))
            # if (np.dot(co_occurrence_matrix[jd_title.lower().lstrip().rstrip().replace(' ','')].tolist(),co_occurrence_matrix[j].T.tolist()) > threshold):
            cosine_similarity_value = cosine_similarity([co_occurrence_matrix[jd_title.lower().lstrip().rstrip().replace(' ','')].tolist()],[co_occurrence_matrix[j].T.tolist()])
            print("The title similarity value is: " + str(cosine_similarity_value))
            if (cosine_similarity([co_occurrence_matrix[jd_title.lower().lstrip().rstrip().replace(' ','')].tolist()],[co_occurrence_matrix[j].T.tolist()]) > threshold):
                print(df[(df.filename == i) & (df.title1 == j)]['title1'].values[0])
                exp += df[(df.filename == i) & (df.title1 == j)]['exp'].values[0]
        if isinstance(jd_exp,int):
            if exp in range(jd_exp -24, jd_exp+25):
                rec_exp.append(i)
        elif isinstance(jd_exp,list):
            if exp in range(jd_exp[0],jd_exp[1]):
                rec_exp.append(i)
    return rec_exp
        

def process_resume_details(names,titles,skills,filenames,degree):
    df=pd.DataFrame({ 'name':names,
                 'titles': titles,
    		     'skills': skills,
                 'filename':filenames,
                 'degree':degree
    		    })
    
    months=['January','February','March','April','May','June','July','August','September','October','November','December']
    processed_title=[]
    experience = []
    for title in df['titles']:
        count=0
        title = title.replace(u'\xa0', u' ')
        for mon in months:
            print(title)
            print(title.find(mon))
            if(title.find(mon)!=-1):
                exp = title[title.find("("):]
                title=title[:title.find(mon)]
                processed_title.append(title)
                experience.append(exp)
                break
            else:
                count+=1
        if(count==12):
            processed_title.append(title)
            experience.append(title)
    
    result=[]
    for title in processed_title:
        count=0
        for mon in months:
            if(title.find(mon)!=-1):
                title=title[:title.find(mon)]
                if(title!=""):
                    result.append(title)
                break
            else:
                count+=1
        if(count==12):
            result.append(title)
    df['experience'] = pd.Series(experience)
    df['title'] = pd.Series(result)
    df = df.drop(['titles'], axis=1)
    df = df[df['title']!=''].copy()
    df['skills'] = df['skills'].apply(look_up_skill)
    df['skills1'] = df['skills'].apply(join_grams)
    df['title1'] = df['title'].apply(lambda x: x.lower().lstrip().rstrip().replace(' ',''))
    df['train1'] = df['title1']+' ' + df['skills1'] 
    df =  df[df['train1'].notna()]
    df['exp'] = df['experience'].apply(extract_months)
    # df = df.drop(['experience'], axis=1)
    
    return df



def jd_exp_extraction(exp):
    print("Extracting experience from JD")
    tokens = word_tokenize(" ".join(exp))
    tokens_pos = pos_tag(tokens)
    
    jd_exp = []
    for np_chunk in cp.parse(tokens_pos):
        if isinstance(np_chunk, nltk.tree.Tree) and np_chunk.label() in ( 'NP1','NP2','NP3','NP4','NP5'):
            noun_phrase = ""
            for (org, tag) in np_chunk.leaves():
                noun_phrase += org + ' '
            
            jd_exp.append(noun_phrase.rstrip())
    # for i in tokens_pos:
    #     val,pos = i
    #     if pos == 'CD' and ('yr' in val or 'year' in val or 'month' in val):
    #             jd_exp.append(val)

    ret = [0]
    for exp in jd_exp:
        if 'yr' in exp.lower() or 'year' in exp.lower() or 'month' in exp.lower():
            tokens_pos = pos_tag(word_tokenize(" ".join([exp.lower()])))      
            for i in tokens_pos:
                val,pos = i
                if pos == 'CD' and '-' not in val and 'month' not in exp.lower():
                    try:                   
                        ret.append(w2n.word_to_num(val.rstrip('+'))*12)
                    except:
                        continue
                elif pos == 'CD' and 'month' not in exp.lower():
                        try:
                            r = [w2n.word_to_num(j)*12 for j in val.rstrip('+').split('-')]
                            ret.append(r)
                        except:
                            continue
                elif pos == 'CD' and 'month' in exp.lower():
                    try:                   
                        ret.append(w2n.word_to_num(val.rstrip('+')))
                    except:
                        continue
    if all(isinstance(sub, type(ret[0])) for sub in ret[1:]):
        return max(ret)
    else:
        return r
    


def resume_recommendation(jd_path,df,threshold = 0.15,topn = 15, co_occ_update = True):
    print("Recommending resumes...")
    jd_dict = extract_jd_details(jd_path)

    jd_dict['Skill'] = look_up_skill(jd_dict['Skill'])

    ## updating cooccurence matrix for jd skills 
    sentences  = ''.join(jd_dict['Title'][0].split()).lower() + " " +join_grams(jd_dict['Skill'])
    if co_occ_update:
        co_occurrence_matrix = co_occ_matrix([sentences])
    else:
        d = pickle.load(open('co_occ_dict.pkl','rb'))
        vocab = set()
        for key, value in d.items():
            vocab.add(key[0])
            vocab.add(key[1])
        vocab = sorted(vocab)
        co_occurrence_matrix = pd.DataFrame(data=np.zeros((len(vocab), len(vocab)), dtype=np.int16),
                      index=vocab,
                      columns=vocab)
        for key, value in d.items():
            co_occurrence_matrix.at[key[0], key[1]] = value
            co_occurrence_matrix.at[key[1], key[0]] = value
			
    data  = join_grams(jd_dict['Skill'])
    
    filenames_s = similar_doc(df,data,topn)
    print("The number of resumes matching by skill is: " + str(len(filenames_s)))
    jd_exp = jd_exp_extraction([' '.join(jd_dict['Exp'])])
    jd_title = ''.join(jd_dict['Title'][0].split()).lower()
    filenames_e = similar_exp(filenames_s,jd_exp,threshold,jd_title,df,co_occurrence_matrix)
    print("The number of resumes matching by experience is: " + str(len(filenames_e)))
    filenames_d = []
    for i in filenames_e:
        filenames_d.append((i,degree_flag(df[df.filename ==i].head(1)['degree'].values[0], jd_dict['Degree'])))
    return filenames_d



###############################################################################

def resume_details(resume_directory,name,new_resume_path = ''):
    names = []
    degree = []
    titles = []
    skills =[]
    filenames = []
    if not os.path.isfile('resume_details.csv'):
        for f in os.listdir(resume_directory):
            path = os.path.join(resume_directory,f)
            print(path)
            try :
                if '.pdf' in path:
                    names,titles,skills,filenames,degree = extract_resume_details(path,names,titles,skills,filenames,degree,name)
            except:
                continue
        df = process_resume_details(names,titles,skills,filenames,degree)
        df.to_csv('resume_details.csv',index=False)
        
        ## generate co variance matrix 
        sentences = list(set(df['train1']))
        
    ##### for new resume give the path in below
    elif os.path.isfile(new_resume_path):
        df = pd.read_csv('resume_details.csv',keep_default_na=False)
        try:
            names,titles,skills,filenames,degree = extract_resume_details(new_resume_path,names,titles,skills,filenames,degree,name)
        except:
            raise Exception("The resume is already present in our system.") 
        df_new = process_resume_details(names,titles,skills,filenames,degree)
        df = pd.concat([df,df_new])
        df.reset_index(drop=True, inplace=True)
        df.to_csv('resume_details.csv',index=False)

        ## update co variance matrix 
        sentences = list(set(df_new['train1']))

    co_occurrence_matrix = co_occ_matrix(sentences)
    return df,co_occurrence_matrix

    
###########################################################################
###########################################################################


############given jd


'''def populate_resume(file_path):
    directory = os.getcwd()
    resume_directory = os.path.join(directory,"Resumes")
    #jd_path = r'D:\Intelligent Systems\Practical Language Processing\Project\coocc_jd\jd_509.txt'
    try:
        df,co_occurrence_matrix =  resume_details(resume_directory,file_path)
    except:
        raise Exception("The resume is already present in our system.")'''
 
###########################################################################
###########################################################################

def trigger_resume_fetching(jd_path,job_id,chat_id):
    df = pd.read_csv('resume_details.csv',keep_default_na=False)
    recom_file = resume_recommendation(jd_path,df,threshold = 0.15,topn = 15)
    return recom_file


def save_resume_in_db(new_resume_path,want_email_flag):
    try:
        name,email,linkedin_contact=extract_name_email_linkedin(new_resume_path,want_email_flag)
        return name,email,linkedin_contact
    except:
        raise Exception("The resume is already present in our system.")
    
def new_resumes_recommendation(new_resume_path,name):
    directory = os.getcwd()

    open_jd = database_updates.get_open_jd()
    resume_directory = os.path.join(directory,"Resumes")

    df,co_occurrence_matrix =  resume_details(resume_directory,name,new_resume_path)

    managerids = []
    candidate_dict={}
    for managerid,filename,title in open_jd:
        path = os.path.join(directory,"job_descriptions",filename+'.txt')
        resume_file_name=os.path.split(new_resume_path)[-1]
        print("Newly entered resume is " + resume_file_name)
        if resume_file_name in [os.path.split(i)[-1] for i,degree in resume_recommendation(path,df,threshold = 0.3,topn = 15,co_occ_update = False)]:
            print("New resume got matched " + resume_file_name)
            candidate_dict['manager_id']=managerid
            candidate_dict['job_id']=filename
            candidate_dict['job_title']=title
            candidate_dict['degree']=degree
            managerids.append(candidate_dict)

    return list(managerids)