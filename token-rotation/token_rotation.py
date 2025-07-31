#!/usr/bin/env python3
# Script to automatically rotate the org tokens within a particular realm in Splunk o11y . 
# Created by Rohit Sharma , PS
import json
import argparse
import subprocess
import requests
from datetime import datetime as dt
import os
import pandas as pd
import keystore
import time
from time import strftime
import smtplib
import sys
from email.mime.text import MIMEText
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import configparser
import keystore
def main(): #The main function that controls the flow of the program.
    """
    Main function to retrieve token expiry data, check which tokens need rotation, and rotate them if necessary.
    """
    # Define argparse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--dry-run', action='store_true', dest='dry_run', help='Only show proposed changes')
    required_named = parser.add_argument_group('Required named arguments')
    required_named.add_argument('-r', action='store', dest='realm', help='Splunk IM Realm', type=str, required=True)
    required_named.add_argument('-d', action='store', dest='days', help='Number of days to check for Token Rotation', type=int, required=True)
    required_named.add_argument('-a', action='store', dest='api_token', help='API Token to authenticate with Splunk O11y', type=str, required=True)
    required_named.add_argument('-t', action='store_true', default=False, dest='rotate_tokens', help='Switch for Token Rotation to True')
    parser.add_argument('-s', '--service', action='store', dest='service', help='Type servicename for storing the password in keyring')
    parser.add_argument('-u', '--username', action='store', dest='username', help='Type username for storing the password in keyring')
    parser.add_argument('-f', action='store_false', default=True, dest='boolean_f', help='Switch for Token Rotation to False')
    required_named.add_argument('-g', action='store', dest='grace_period', help='Grace Period in days', type=int, required=True)

    # Parse command line arguments
    args = parser.parse_args()

   

    # Store the password in the keyring
    service = args.service 
    username = args.username
    keystore.store_password(service, username)

    # Check the stored password against user input
    check_password(service, username)

     # Check grace period is not more than 60 days
    check_grace_period(args.grace_period)

    # Get token expiry data for all tokens in the given realm
    df = get_token_expiry_data(args.api_token, args.realm, args.days)
    

    # Check which tokens need rotation
    tokens_to_rotate = df[df['remaining'] < args.days * 24 * 60 * 60]
    df = df[df.columns.difference(['created', 'creator', 'description',
                                   'disabled', 'exceedingLimits', 'limits', 'notifications', 'permissions','id','lastUpdatedBy'])]
    
    # Rotate tokens if necessary
    if args.rotate_tokens and not args.dry_run :
        for _, row in df.iterrows():
            if row['remaining'] > args.days * 24 * 60 * 60:
                data = 'Token '+row['name']+' need no rotation'
                write_to_log(data)

            else:
                rotate_tokens(args.api_token,args.realm, args.grace_period, row['name'])
    elif args.dry_run:
        print("Tokens that need rotation:")
        print(tokens_to_rotate[['name', 'expiry','remaining','Expiry_Date']].to_string(index=False))
    else:
        write_to_log("No tokens need rotation.")

#This function retrieves token expiry data for all tokens in the given realm and returns it as a pandas DataFrame. The requests library is used to make a GET request to the Splunk O11y API to retrieve the token data. The response is then saved to a local file named token.json. The data is then loaded from the file and converted to a pandas DataFrame, which is returned by the function.
def get_token_expiry_data(api_token: str, realm: str, days: int) -> pd.DataFrame:
    """
    Get the expiry data for all tokens in the given realm.

    :param api_token: The SignalFx API token to use for authentication.
    :param realm: The SignalFx realm where the tokens are located.
    :param days: The number of days before a token expires that it should be rotated.
    :return: A Pandas DataFrame containing the expiry data for all tokens in the given realm.
    """
    # Load the token data from the API
    token_data = load_token_data(api_token, realm)

    # Convert the token data to a DataFrame
    tokens_df = pd.json_normalize(token_data["results"])
    

    # Calculate the remaining time for each token
    tokens_df["remaining"] = (tokens_df["expiry"] / 1000) - time.time()
    tokens_df["expiry_Seconds"] = (tokens_df["expiry"].floordiv(1000))
    tokens_df["Expiry_Date"] = pd.to_datetime(tokens_df['expiry_Seconds'],  unit='s').dt.date
    

    return tokens_df



#This function rotates the expired tokens in the given realm by calling the get_token_expiry_data() function to retrieve the token data and then processing it to identify the expired tokens. For each expired token, a new token is created and the old token is deleted. The new token is then saved to a local file named token.csv. If dry_run is True, the function only prints the tokens that would be rotated without actually rotating them. If dry_run is False, the function rotates the tokens.
def update_token(name, realm, api_token, grace_period):
    url = f"https://api.{realm}.signalfx.com/v2/token/{name}/rotate?graceful={grace_period}"
    headers = {"Content-Type": "application/json", "X-SF-TOKEN": api_token}

    response = requests.post(url, headers=headers)

    if response.status_code != 200:
        write_to_log(f"Failed to update token {name}. Status code: {response.status_code}")
        return False

    write_to_log(f"Token {name} updated successfully.")
    return True



def rotate_tokens(api_token, realm, grace_period, token_name) -> bool:
    
    # Load token data from file
    token_data = load_token_data(api_token, realm)

    # Get token data for the specified token
    tokens_df = pd.json_normalize(token_data["results"])
    token = tokens_df[tokens_df["name"] == token_name]
    
    # Check if the token exists
    if token.empty:
        write_to_log(f"No token found with name {token_name}")
        return False
    
    # Call the update_token function to rotate the token
    if update_token(token_name, realm, api_token, grace_period):
        return True
    
    write_to_log(f"Failed to rotate token {token_name}.")
    return False


def load_token_data(api_token, realm):

    
    try:
        response = requests.get(
            f'https://api.{realm}.signalfx.com/v2/token/',
            headers = {
                'Content-Type': 'application/json',
                'X-SF-TOKEN': api_token
            }
        )
        if response.status_code != 200:
            write_to_log(f'Error loading token data. Status code: {response.status_code}')
            return None

        data = response.json()
        with open('token.json', 'w') as f:
            json.dump(data, f)

        return data

    except requests.RequestException as e:
        write_to_log(f'Error loading token data: {e}')
        return None

# You might need to define the write_to_log function




#This function checks the password for the given service and username using the keyring library and the bcrypt library. The password is read from a local file named auth.txt. If the password is correct, the function continues. If the password is incorrect, the function exits the program.
def check_password(service, username):
    """
    This function prompts the user for a password and checks it against the password stored in the keystore
    for the given service and username using the bcrypt library.

    Parameters:
    service (str): The name of the service for which the password is stored.
    username (str): The username for which the password is stored.

    Returns:
    None
    """

    import bcrypt
    import getpass
    import sys

    stored_password = keystore.get_password(service, username)
    if stored_password is None:
        print(f"No password found for {service}/{username}")
        sys.exit(1)

    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(stored_password.encode(), salt)

    user_password = getpass.getpass("Enter your password: ")
    if bcrypt.checkpw(user_password.encode(), hashed_password):
        print("Password match!")
    else:
        print("Incorrect password, exiting...")
        sys.exit(1)

#This function sends an email with the given body using the information in the config.ini file. The smtplib library is used to send the email.
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(realm, expired_tokens):
    # read configuration file
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    # get email configuration
    email_config = config['EMAIL']
    from_address = email_config['from_address']
    to_address = email_config['to_address']
    smtp_server = email_config['smtp_server']
    smtp_port = email_config.getint('smtp_port')
    smtp_username = email_config.get('smtp_username')
    smtp_password = email_config.get('smtp_password')

    # create email message
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg['To'] = to_address
    msg['Subject'] = f'Token Expiry Notification for {realm}'
    body = f'The following tokens have expired:\n\n{expired_tokens}'
    msg.attach(MIMEText(body, 'plain'))

    # send email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        if smtp_username and smtp_password:
            server.login(smtp_username, smtp_password)
        server.sendmail(from_address, to_address, msg.as_string())



import os
import datetime

#This function writes the given data to a local file named rotation.log.

def write_to_log(data):
    """
    This function appends the given data to a log file with the current date as its name in the "logs" directory.

    Args:
        data: A string containing the data to be written to the log file.

    Returns:
        None
    """
    # Create the logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # Get the current date and time
    now = datetime.datetime.now()

    # Create the log file name using the current date and time
    log_file_name = now.strftime("%Y-%m-%d") + ".log"

    # Append the data to the log file
    with open(os.path.join("logs", log_file_name), "a") as log_file:
        log_file.write(str(now)+' '+data + "\n")
#This function checks the value of grace_period to ensure that it is between 0 and 60. If the value is outside of this range, the function exits the program.
def check_grace_period(grace_period):
    """
    Check if the grace period is within a valid range.

    Parameters:
    grace_period (int): the grace period in minutes.

    Returns:
    None.

    """
    if grace_period < 0:
        print("Error: Grace period cannot be negative.")
        sys.exit(1)
    elif grace_period > 60:
        print("Error: Grace period cannot be more than 60 days.")
        sys.exit(1)




if __name__ == '__main__':
    main()


