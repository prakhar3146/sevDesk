########################################################### Importing Packages #############################################################################################################################################################
from flask import Flask, render_template, jsonify, request
import main
import os, sys
import re
from utils import write_text_file as log
############################################################################################################################################################################################################################################


########################################################### Initializing Global Variables #################################################################################################################################################
templates_folder_path = os.path.join(os.getcwd(),"templates")
print("TEMPLATES Folder : ", templates_folder_path)
sys.path.append(templates_folder_path)

app = Flask(__name__, static_folder="static")

email_id_list= []
log(input_filepath="reports/email_ids_for_notification.txt",data="",separator="\n")
##########################################################################################################################################################################################################################################

########################################################### Custom Routes And Functions #################################################################################################################################################################################
@app.route("/")
def welcome():
    return render_template("index.html")



@app.route('/execute-workflow', methods=['POST'])
def execute_workflow():
    # Calling the main function in main.py to start the sync
    
    result, error_type = main.main(email_id_list)
    if result== "success" and error_type=="no_action_needed":
        return jsonify({'result': f"Workflow executed successfully but no records were found that needed to be synced!"})
    elif result== "success":
        return jsonify({'result': f"Workflow executed successfully and records were updated!"})

@app.route('/submit', methods=['POST'])
def submit_email():
    # Adding email id's entered by the user to notification email id list and displaying the status in the UI
    global email_id_list
    data = request.json
    input_value = data.get('value')
    print("An email was added :", input_value,"\n to the list : ",email_id_list)
    #Verifying the format of the entered email
    pattern = "^[\w! # $ % & ' * + - / = ? ^ _.]+[@][A-za-z]+\.[A-za-z]{1,3}$"
    if re.fullmatch(pattern=pattern, string=input_value):
        email_id_list.append(input_value)
        log(input_filepath="reports/email_ids_for_notification.txt",data=input_value,separator="\n", mode="a")
        return jsonify({'result': f"{input_value} was added to the mailing list"})
    else:
        return jsonify({'result': f"Unable to add - {input_value} to the mailing list! Please check the email id you entered!"})
    
##################################################################################################################################################################################################################################################################################################################################################################    


if __name__ == '__main__':
    app.run(host ="127.0.0.1", debug=True, port= 5000)
