# ****************************************************** Begining of document ***************************************************************************************************************************************************************************************************************************************************************************************************************************************************8888


########################################################## Project details ###############################################################################################################################################################################################################
"""
Developers :  Prakhar Prakash
Developer contact : mr.prakhar@gmail.com, +919625708656
Last updated at :  03-03-2025 at 04:53 (IST)
Project name : sevDesk to HubSpot sync
Project repository address GitHub :
Project goal : Every contact created in sevDesk with an email id associated with it, has to be automatically synced to HubSpot
Solution steps :
                  (1) Fetch all contacts from each category from the 'sevDesk' API,
                  (2) Loop over each contact fetched from the 'sevDesk' API and
                            fetch the email id associated with each of the contacts from the email API endpoint,
                  (3) Fetch all contacts from Hubspot
                  (4) Reconcile the contacts fetched from both HubSpot and sevDesk API ,
                             generate reports accordingly and create the contacts which are not present in HubSpot,
                  (5) Send an email consisting of all the necessary reports as an attachment, to the concerned parties
                  NOTE :  The contacts for which the associated emails are found, are to be created in HubSpot,


"""
########################################################## Projet details - END ###############################################################################################################################################################################################################


############################################################### Importing the required modules and packages ##################################################################################################################################################################################
import datetime

import pandas as pd
import requests, os
from utils import retry_until_condition_is_satisfied, write_text_file, create_dir_if_not_exists, \
    prepare_email_template_and_send, \
    rename_and_move
import json
import time
from hubspot import HubSpot
from hubspot.crm.contacts import SimplePublicObjectInput, ApiException
import traceback
from dotenv import load_dotenv


############################################################### Importing the required modules and packages ##################################################################################################################################################################################

# Loading the dotenv package to load the .env variables
load_dotenv()



#################################################### Defining custom functions ##################################################################################################################################################################################################################################################################################################################################

# This function takes 3 inputs :  (1) sevDesk API endpoint url, (2)The required headers for authentication, (3)The payload/filters
### This function returns the output in three parts namely, (1) status('success'/'failed') , (2)error_type(custom error_types) and (3) A list of outputs that need to be returned by the function which in this case will be the reponse object if the response returned from the API is 200 , otherwise it will return an error message
def fetch_contact_info_from_sevdesk(url, headers, payload):
    try:

        response = requests.request("GET", url, headers=headers, data=payload)
        # print("Status : ", response.status_code)
        # print(response.text)
        status = response.status_code
        if status == 200:
            return "success", "", [response]
        else:
            return "failed", "connection_error", [
                f"Failed to establish a connection to the API, The response code was : {status}"]
    except Exception as e:
        print("Exception occured while Connecting to the API", e)
        return "failed", "technical_error", [
            f"Exception occured while establishing a connection to the API: {e}"]


# This function takes 3 inputs :  (1) HUBSPOT API endpoint url, (2)The required headers for authentication, (3)The payload/filters
## This function returns the output in three parts namely, (1) status('success'/'failed') , (2)error_type(custom error_types) and (3) A list of outputs that need to be returned by the function which in this case will be the reponse object if the response returned from the API is 200 , otherwise it will return an error message
def fetch_contact_info_from_hubspot(url, headers, payload={}):
    try:

        response = requests.request("GET", url, headers=headers, data=payload)
        # print("Status : ", response.status_code)
        # print(response.text)
        status = response.status_code
        if status == 200:
            return "success", "", [response]
        else:
            return "failed", "connection_error", [
                f"Failed to establish a connection to the API, The response code was : {status}"]
    except Exception as e:
        print("Exception occured while Connecting to the API", e)
        return "failed", "technical_error", [
            f"Exception occured while establishing a connection to the API: {e}"]


# This function will parse the data fetched from the sevDeskAPI, add a marker(column name : 'entity_type') to classify individuals and organizations , loop over each contact fetched from the sevDesk API and fetch the email id's for them.
# NOTE : Only the contacts for which an associated email id's are found present in sevDesk, will be considered for creation in HUBSPOT (Reason: It is recommended in the HUBSPOT API documentation)
## This function returns the output in three parts namely, (1) status('success'/'failed') , (2)error_type(custom error_types) and (3) A list of outputs that need to be returned by the function which in this case will be ,the list of contacts for which the email id was found in case of success , otherwise it will return an error message
def parse_reponse_data(contact_data):
    try:
        # contact_data = response.json()["objects"]
        print("Number of contacts fecthed : ", len(contact_data))
        list_of_reconciled_contacts = []

        # Segregating Organizations and Individuals
        for contact in contact_data:
            print("Contact : ", contact['name'])
            contact_id = contact['id']
            entity_type = "individual" if contact['name'] is None else "organization"
            if entity_type not in ["individual", "organization"]:
                continue

            email_url = "https://my.sevdesk.de/api/v1/CommunicationWay"
            email_payload = f"contact%5BobjectName%5D=Contact&contact%5Bid%5D={contact_id}&type=EMAIL"
            ##### Fetching Email Id's for every contact #####
            status, error_type, sevdesk_email_api_response = retry_until_condition_is_satisfied(
                function_name=fetch_contact_info_from_sevdesk,
                argument_list=[email_url, headers, email_payload], time_until_retry=4, no_of_retries=5,
                value_to_be_satisfied="success")
            if status != "success":
                return status, error_type, [f"Failed to retrieve the email id for {contact_id}",
                                            sevdesk_email_api_response]
            email_data = sevdesk_email_api_response[0].json()["objects"]
            # print(f"Email data retrievd for :{contact_id} \n is: {email_data}")
            if len(email_data) == 0:
                continue
            email_id = email_data[0]['value']
            contact['email_id'] = email_id
            contact['response_status'] = "success"
            contact['entity_type'] = entity_type

            list_of_reconciled_contacts.append(contact)
        return "success", "", list_of_reconciled_contacts
    except Exception as e:
        print(f"Exception when Creating contacts main: {e}")
        traceback.print_exc()
        return "failed", "technical_error", [f"{e}"]


# This is a function to create a new contact in HubSpot
###This function returns a "success" or a "failed" depending on the response code returned to the POST request to the HubSpot API
def create_contact_hubspot(url_hub, headers_hub, attributes_dict: dict):
    try:
        # Create the contact
        # contact = api_client.crm.contacts.basic_api.create(SimplePublicObjectInput(**attributes_dict))
        # print(f"Contact created with ID: {contact.id}")
        payload = json.dumps(attributes_dict)

        response = requests.request("POST", url_hub, headers=headers_hub, data=payload)
        print("Creation Status : ", response.status_code)
        # print("Creation Response : ", response.text)
        if response.status_code != 201:
            return "failed"
        return "success"
    except ApiException as e:
        print(f"Exception when creating contact: {e}")
        return "failed"
    except Exception as exp:
        print(f"Exception when creating contact: {exp}")
        return "failed"



#This function fetches and adds the missing contacts to hubspot after reconciliation with sevDesk
## This function returns the output in three parts namely, (1) status('success'/'failed') , (2)error_type(custom error_types) and (3) A list of outputs that need to be returned by the function which in this case will be a remark regarding the sync status or an error message
def fetch_contact_info_from_hubspot_and_create(api_client_hubspot, sevdesk_contact_df):
    try:
        # Fetch all contacts
        print("The sevdesk contacts : ", sevdesk_contact_df.columns)
        sevdesk_contact_df.drop_duplicates(subset='email_id', inplace=True)
        all_contacts = api_client_hubspot.crm.contacts.get_all()
        # Connecting to hubspot api
        # hub_response = fetch_contact_info_from_hubspot(hubspot_url,hubspot_headers)

        sevdesk_emails = set(sevdesk_contact_df['email_id'])

        hubspot_emails = []
        hubspot_conatcts = []
        for contact in all_contacts:
            # print("Keys : ", contact.properties.keys())
            hubspot_email = contact.properties.get('email')  # contact['properties']['email']
            hubspot_firstname = contact.properties.get('firstname')
            hubspot_lastname = contact.properties.get('lastname')
            hubspot_hs_object_id = contact.properties.get('hs_object_id')
            hubspot_emails.append(hubspot_email)
            hubspot_conatcts.append(
                {"email": hubspot_email.strip() if hubspot_email is not None else "",
                 "firstname": hubspot_firstname.strip().title() if hubspot_firstname is not None else "",
                 "lastname": hubspot_lastname.strip().title() if hubspot_lastname is not None else "",
                 "object_id": hubspot_hs_object_id if hubspot_hs_object_id is not None else ""})

        hubspot_emails = set(hubspot_emails)
        hubspot_contact_df = pd.DataFrame(hubspot_conatcts)
        hubspot_contact_df.to_csv("reports/Hubspot_existing_contacts.csv", index=False)
        emails_to_be_created = list(sevdesk_emails - hubspot_emails)
        additional_emails_in_hubspot = hubspot_emails - sevdesk_emails

        print("Email id not present in Hubspot : ", emails_to_be_created)
        print("Email id not present in sevdesk : ", list(additional_emails_in_hubspot))
        print("The sevdesk contacts : ", sevdesk_contact_df.columns)

        if len(emails_to_be_created) == 0:
            return "success", "no_action_needed", ["sevDesk and HubSpot already in Sync!"]
        write_text_file("reports/Hubspot Contact Onboarding.txt", data="\n".join(emails_to_be_created),
                        success_message="success",
                        separator="Email to be created :\n", failure_message="failed")
        # Creating email id's
        successful_creations_list = []
        failed_creations_list = []
        for email in emails_to_be_created:
            contact_data = sevdesk_contact_df.loc[sevdesk_contact_df["email_id"] == email]
            contact_data.reset_index(drop=True, inplace=True)
            # print("Onboard data : ", contact_data)
            first_name = contact_data.get(key="surename")[0]
            last_name = contact_data.get(key='familyname')[0]
            email_id_onboard = contact_data.get(key='email_id')[0]
            # Define the contact properties
            contact_properties = {
                "properties": {
                    "firstname": first_name,
                    "lastname": last_name,
                    "email": email_id_onboard,
                    # "phone": "555-555-5555"
                    "company": "HubSpot",
                    "website": "hubspot.com",
                    "lifecyclestage": "customer"
                }
            }
            # if not first_name:
            #     del contact_properties['firstname']
            # if not last_name:
            #     del contact_properties['lastname']
            print("Creating : ", contact_properties)
            creation_status = create_contact_hubspot(url_hub=hubspot_url, headers_hub=hubspot_headers,
                                                     attributes_dict=contact_properties)  # create_contact_hubspot(api_client_hubspot, contact_properties)
            if creation_status == "failed":
                failed_creations_list.append(contact_properties['properties'])
                # return "failed", "technical_error", [f"Failed to create contact for : {email} in Hubspot!"]
            else:
                successful_creations_list.append(contact_properties['properties'])

        success_log_df = pd.DataFrame(successful_creations_list)
        failed_log_df = pd.DataFrame(failed_creations_list)
        success_log_df.to_csv("reports/Success_boarding_hubspot.csv", index=False)
        failed_log_df.to_csv("reports/Failed_boardings_hubspot.csv", index=False)
        return "success", "", ["Records were created in HubSpot! "]
    except ApiException as e:
        print(f"Exception when creating contacts: {e}")
        return "failed", "api_error", [f"Error: {e}"]
    except Exception as ex:
        print(f"Exception when Creating contacts main: {ex}")
        traceback.print_exc()
        return "failed", "technical_error", [f"{ex}"]


#################################################### Defining custom functions - END ##################################################################################################################################################################################################################################################################################################################################


########################### Initializing global variables ###############################################################################################################

# Initializing the HubSpot client with the access token
api_key = os.getenv("HUBAPI")

api_client = HubSpot(access_token=api_key)


# Fetching the sevDesk URL from the environment variables
url = os.getenv("SEVURL")

# Preparing the headers for Authentication
headers = {
    'Username': os.getenv("SEVUSERNAME"),
    'PW': os.getenv("SEVPASSWORD"),
    'Content-Type': 'application/x-www-form-urlencoded',
    'Authorization': os.getenv("SEVAPI"),
    'Cookie': '__cf_bm=GcAdsFZsmGo4_tBInUdlNeOwlW4oaBhu8lJ4HIbGiPc-1740439148-1.0.1.1-fOV4iCFw1Z8x5dDSF1D7Nmtix225rvk7wHGrfOwbUClP4.1BO3WlqW_GDW6bN95TBFMLdy81gTPa8zjaBkClVA'
}

# Fetching HUBSPOT credentials
hubspot_url = os.getenv("HUBURL")
hubspot_payload = {}
hubspot_headers = {
    'Username': os.getenv("HUBUSERNAME"),
    'PW': os.getenv("HUBPASSWORD"),
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {api_key}',
    'Cookie': '__cf_bm=WaXICay4uq6up8yiGIurvbKPukWno7cWhaR18uVuSKo-1740490833-1.0.1.1-giocpmY3RILepANSYjP065lVkB2Y2_Fy5OZpzuS1Tl1KDpr55ikelfc.Ol1SEN6GnO5Y2GRs5WDpDBzDkRMxYg'
}


########################### Initializing global variables - END ###############################################################################################################


################################################### Main function ####################################################################################################################################################################################################
def main(email_notification_id_list):
    try:
        # Initializing default variables
        error_type = ""
        status = None
        sevdesk_api_response = None

        # Defining the list of categories by Id that are to be fetched from the Contacts from sevDesk and Hubspot
        list_of_categories_to_be_fetched = ["1", "2", "3", "4"]
        list_of_contacts_fetched_sevdesk = []

        ############################################################ SevDesk data preparation #######################################################################################################################################################################

        # Looping over categories by their id's one by one and fetching the response from the sevDesk API
        for id_cat in list_of_categories_to_be_fetched:
            payload = f'category%5Bid%5D={id_cat}&category%5BobjectName%5D=Category&orderByCustomerNumber=ASC%2FDESC&depth=0%2C1'
            status, error_type, sevdesk_api_response = retry_until_condition_is_satisfied(
                function_name=fetch_contact_info_from_sevdesk,
                argument_list=[url, headers, payload], time_until_retry=4, no_of_retries=5,
                value_to_be_satisfied="success")
            if status == "success":
                fetched_sevdesk_contact_list = sevdesk_api_response[0].json()['objects']
                if len(fetched_sevdesk_contact_list) > 0:
                    list_of_contacts_fetched_sevdesk.extend(fetched_sevdesk_contact_list)

        ############################################################ SevDesk data preparation - END #######################################################################################################################################################################

        ############################################################ HUBSPOT operations section #######################################################################################################################################################################
        if status == "success":

            # logging the contact data fetched from the sevDesk API
            sevdesk_all_contacts_df = pd.DataFrame(list_of_contacts_fetched_sevdesk)
            sevdesk_all_contacts_df.to_csv("reports/All_contacts_sevdesk.csv", index=False)

            status, error_type, reconciled_list = parse_reponse_data(list_of_contacts_fetched_sevdesk)
            print("Executed \n", status, error_type, reconciled_list)
            if status == "success":

                sevdesk_contact_df = pd.DataFrame(reconciled_list)
                sevdesk_contact_df.to_csv("reports/sevdesk_email_api_response_data.csv", index=False)
                final_status, error_type, hubspot_api_response = retry_until_condition_is_satisfied(
                    function_name=fetch_contact_info_from_hubspot_and_create,
                    argument_list=[api_client, sevdesk_contact_df], time_until_retry=4, no_of_retries=5,
                    value_to_be_satisfied="success")
                status = final_status
                print("Creation Status : ", final_status, error_type)
                if final_status == "success" and error_type == "no_action_needed":
                    print("No records need to be inserted!")
                    write_text_file(input_filepath=f"reports/final_status_{final_status}.txt",
                                    data=f"The process ended with final status: {final_status} with remark type : {error_type} \n Description/remarks : No Records need to be created in HubSpot. Already in Sync!")
                elif final_status == "success":
                    print("Contacts created successfully in HubSpot!")
                    write_text_file(input_filepath=f"reports/final_status_{final_status}.txt",
                                    data=f"The process ended with final status: {final_status} with remarks : {error_type} \n API response : \n{hubspot_api_response[0]}")

                else:
                    write_text_file(input_filepath=f"reports/final_status_{final_status}.txt",
                                    data=f"The process ended with final status: {final_status} with error type : {error_type} \n error message : \n{hubspot_api_response[0]}")
                status= final_status
            
            else:
                print(
                    f"Contact Data fetched from the sevDesk API could not be validated/parsed!. The error type was : {error_type} \n with the error message {reconciled_list}")

                write_text_file(input_filepath=f"reports/final_status_{status}.txt",
                                data=f"Contact Data fetched from the sevDesk API could not be validated/parsed!. The error type was : {error_type} \n with the error message {reconciled_list}")
                return status, error_type
        else:
            print(
                f"Contact Data could not be fetched from the sevDesk API. The error type was : {error_type} \n with the error message {sevdesk_api_response}")
            print("No records need to be inserted!")
            write_text_file(input_filepath=f"reports/final_status_{status}.txt",
                            data=f"The process ended with final status: {status} with remarks : {error_type} \n API response : \n{sevdesk_api_response[0]}")

        write_text_file(input_filepath=f"reports/final_status_{status}.txt",
                        data=f"The main function executed successfully with status : {status}!. The remark was : {error_type}")
        reciever_email_list = ["mr.prakhar@gmail.com"]
        #Adding the custom email id's for notifications that were entered by the user
        reciever_email_list.extend(email_notification_id_list)
        print("The email id's are ",reciever_email_list)
        credentials_dict = {'invite_template_path': "templates/email_template.html", 'sender': os.getenv("SENDERMAIL"),
                            'secret_key': os.getenv("SENDERPASSKEY"), 'port': 587,
                            'password': os.getenv("SENDEREMAILPASSWORD"),
                            'subject': f"The sevDesk to HubSpot contacts sync was : {status}", 'host_domain_link': "",
                            'receiver': ', '.join(reciever_email_list),
                            'notification_type': f"contacts_creation_{status}",
                            "reports_folder_path": "reports",
                            'list_of_report_names': ["Success_boarding_hubspot.csv", "Failed_boardings_hubspot.csv",
                                                     "final_status_success.txt", "final_status_failed.txt"]}
        reports_folder_path = credentials_dict["reports_folder_path"]
        send_notification = prepare_email_template_and_send(credentials_dict)
        print("EMAIL Notification status : ", send_notification)
        time.sleep(5)
        counter = 0
        # Moving the generated reports to the archive folder
        current_directory = os.getcwd()
        reports_folder_path = os.path.join(current_directory, reports_folder_path)
        # Creating the archive folder with the timestamp
        output_folder_name = f"archive/archive_{datetime.datetime.now().strftime('%d_%m_%Y_%H_%M_%S')}"

        print("Folder creation status : ",
              create_dir_if_not_exists(folder_creation_path=current_directory, foldername=output_folder_name))
        reports_generated = os.listdir(reports_folder_path)
        print("Number of generated logs/reports : ", len(reports_generated))
        for filename in reports_generated:
            input_filepath = os.path.join(reports_folder_path, filename)

            output_filepath = os.path.join(current_directory, output_folder_name, filename)
            archival_status = rename_and_move(input_filepath=input_filepath, output_filename_and_path=output_filepath)
            if archival_status == "success":
                counter += 1
        if len(reports_generated) == counter:
            print(" All reports archived !", counter)
        # print(" reports archived !", counter,"\n total",re)
        return status, error_type
    except Exception as exp:
        print("Exception in main!", exp)
        traceback.print_exc()
        write_text_file(input_filepath=f"reports/final_status_failed.txt",
                        data=f"There was an exception in the the main function !. The error was : {exp}")
        return "failed","technical_error"

    ############################################################ HUBSPOT operations section - END #######################################################################################################################################################################


################################################### Main fuction - END ####################################################################################################################################################################################################
# if __name__ == "__main__":
#     main()

# ****************************************************** End of document ***************************************************************************************************************************************************************************************************************************************************************************************************************************************************8888
