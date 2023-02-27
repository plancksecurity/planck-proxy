import email
from email import *
import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from conftest import *


# def get_email_body(email_string, tmp_path):
#     mail = email.message_from_string(email_string)
#     if mail.is_multipart():
#         for payload in mail.get_payload():
#             # if payload.is_multipart(): ...
#             print payload.get_payload()
#     else:
#         print b.get_payload()



def get_email_body(email_string, tmp_path):
    path = tmp_path['tmp']
    path = os.path.join(path, "temp_eml.txt")

    def save_string_to_file(email_string):
        path = tmp_path['tmp']
        path = os.path.join(path, "temp_eml.txt")
        save_file = open(path, "w")
        save_file.write(email_string)
        save_file.close()
    
    save_string_to_file(email_string)

    email_file = open(path, "r")
    email_parser = email.parser.Parser()
    parsed_string = email_parser.parse(email_file)
    return parsed_string.get_payload()





# def get_email_body(emailobj):


#     def _get_body(emailobj):
        
#         if emailobj.is_multipart():
#             for payload in emailobj.get_payload():
                
#                 if payload.is_multipart():
#                     return _get_body(payload)

#                 body = payload.get_payload()
#                 if payload.get_content_type() == "text/plain":
#                     return body
#         else:
#             return emailobj.get_payload()

#     body = _get_body(emailobj)

#     return body