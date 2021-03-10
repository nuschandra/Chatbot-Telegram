import re
import spacy
from nltk.corpus import stopwords

nlp_model = spacy.load('jd_model')
nlp_exp_model = spacy.load('jd_exp_model')
mystopwords=stopwords.words("English") + ['experience','computer,','science','expert','knowledge','plus','proficiency','understanding','excellent','ability','skill','responsibility']

def pre_process(text):

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
    result = {"degree": degree,
              "exp"   : exp,
              "title" : title,
              "skills": skill}
    for key in result:
        print(key.upper()+":")
        for i in result[key]:
            print(i)
        print()
    return(result)


text = """Data Engineer
The Technology Group manages and exploits information technologies to enhance GIC’s ability to be the leading global long-term investment firm. It aims to provide users with empowering and transformational capabilities, and to create an inclusive, innovative and integrated work environment.

We are looking for a dynamic, self-motivated and technically competent individual to join us as Associate/AVP, Data Engineer. You’ll be specialising in the data domain, involve in a high-pace data engineering team that is delivering and supporting GIC data needs.

Responsibilities

· Work closely with data analysts and business end-users to implement and support data platforms using best-of-breed technology and methodology.

· Conduct requirement workshop with stakeholders and analyse requirements holistically.

· Design robust and scalable solutions to meet business needs and takes operational considerations into account. Demonstrate technical expertise in the assigned area.

· Analyse, tackle and resolve day-to-day operational incidents and advisory to business users

· Analyse systems operations data (SLAs, customer satisfaction, delivery quality, team efficiency etc.) to identify actionable trends for continual improvements.

· Play an active role in the project coordinating between internal resources and third parties/vendors for project execution.

Associate/AVP, Data Engineer, Data Platform Engineering
Requirements
• Bachelor’s degree in Computer Science, Computer Engineering or equivalent
• Minimum 2 years of relevant working experience in data modelling and data integration, preferably in an investment and banking environment.
• Familiar with enterprise databases using database technologies (PL/SQL, SQL)
• Good knowledge of Linux family of operating systems.
• Exposure and knowledge in any of the following technologies is advantageous:

- AWS

- Data Visualisation – Tableau

- Data Storage & Processing – SnowFlake

- Data Virtualisation - Denodo

- Programming and Scripting Language

- Python

- Java/Scala

- Shell Script

- RESTful Data API
• Experienced with the Systems Development Life Cycle implementation methodology (SDLC) and/or agile methodologies like Scrum and Kanban.
• A pro-active team player, with strong analytical skills and enjoy complex problem solving with innovative ideas.
• Ability to work closely with data analysts, business end-users and vendors to design and develop solutions.
• Understand the importance of data integrity and accuracy, which are key essentials for our business operations
"""

pre_process(text)