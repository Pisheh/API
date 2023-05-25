from mongoengine import *
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum

    
class Answer(Document):
    content = StringField()
    score = IntField()
    
class Question(Document):
    question = StringField()
    answers = EmbeddedDocumentListField(Answer)
    
class Exam(Document):
    id = ObjectIdField(primary_key=True)
    url = URLField()
    questions = EmbeddedDocumentListField(Question)
    questions_count = IntField()
    
class Skill(Document):
    id = ObjectIdField(primary_key=True)
    title = StringField()
    desc = StringField()
    exam = ReferenceField(Exam)     # many to one

class Seeker(Document):
    id = ObjectIdField(primary_key=True)
    email = EmailField()
    password_hash = StringField()
    firstname = StringField()
    lastname = StringField()
    phone_number = StringField(r'09\d{9}')
    address = StringField()
    cv = EmbeddedDocumentField("CV")
    
    
    def verify_password(self, password):
        check_password_hash(self.password_hash, password)
        
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

class CV(Document):
    content = StringField()
    skills = ListField(ReferenceField(Skill))
    scores = ListField(IntField)