# Splunk O11y Org token Rotation 
# Description

This is a python script which automatically rotates the org token in a Splunk observability realm by comparing the number of days remaining( From the current date) for a token to expire and number of days supplied as an argument(-d) . If number of days for token expiry are less than number of days supplied with "-d" the script will rotate the tokens with a grace period(days) which is also supplied at script run ( -g)  . Most importantly , Please use -n option to dry run the script to see the tokens which are going to get rotated, the dry run will not change anything in your environment. The scripts expects some required arguments . Please run with -h option to learn more. Before running this script in Production environment, try it out by creating some sample org tokens in a trial Splunk O11y org. Link to request : [Splunk O11y Trial](https://www.splunk.com/en_us/download/o11y-cloud-free-trial.html?utm_campaign=google_amer_en_search_brand&utm_source=google&utm_medium=cpc&utm_content=O11y_Cloud_Trial&utm_term=splunk%20observability&_bk=splunk%20observability&_bt=519215939673&_bm=p&_bn=g&_bg=111780047679&device=c&gclid=CjwKCAjw_MqgBhAGEiwAnYOAemEpo0Y04A9KtTe57d-Ln66LS6svOmPW48IpG3NQ_Afz6A6EhN5kTBoCRNAQAvD_BwE)

## Purpose 
Splunk o11y org tokens are the way to authenticate the systems to talk to Splunk o11y backends and send Observability data . Whenever a token is near its expiry they must be rotated with an additional grace period to prevent any disruptions in smooth data injestion. The grace period enables continuous usage of the old tokens as well as new until the grace period ends, post that the new tokens must be updated on the end clients(servers, k8s cluster etc ) to let them send data using the new tokens. Learn More about tokens: [here](https://docs.splunk.com/Observability/admin/authentication-tokens/tokens.html)


## Installation
1. Install ```Python 3.x``` on your system.
2. Clone this repository to your local machine.
3. Install the required packages listed in the requirements.txt file by running `pip3 install -r requirements.txt`.
4. Edit the config.ini file to include the necessary configuration details for sending email notifications(Optional).
5. Create a virtual environment (optional).

## Usage
Arguments
The program takes several arguments as input:

| Argument   | Description  | 
|-------|-------|
| -n, --dry-run | Only show proposed changes. | 
| -r, --realm   | Splunk IM Realm (required). |
| -d, --days    | Number of days to check for Token Rotation (required). |
| -a, --api-token | API Token to authenticate with Splunk O11y (required). |
| -t, --rotate-tokens | Switch for Token Rotation to True (optional). |
| -s, --service | Type servicename for storing the password in keyring (optional). |
| -u, --username | Type username for storing the password in keyring (optional). |
| -f, --boolean_f | Switch for Token Rotation to False (optional). |
| -g, --grace-period | Grace Period in days (required). |
## Running the Program
Open the command prompt or terminal.
Navigate to the directory where the program is saved.
Run the program with the required arguments.
Example usage: `python token_rotation.py -r myrealm -d 30 -a mytoken -t -s myservice -u myusername -g 5`

## Configuration
To securely store your password, this program uses the keyring package. The password is read from an environment variable AUTH_PASSWORD, which should be set in your system's environment variables or in your IDE's run configuration.

To store the password in the keyring, use the optional arguments -s and -u. These will be used as the service name and username, respectively, to identify the password in the keyring. The script also uses another module `keystore.py` module to store and retrieve password from the keyring. 

Instead of using above approach of saving passwords in `environment` variable, there are options to use `AWS Secrets Manager` . Just update the code accordingly. 

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
