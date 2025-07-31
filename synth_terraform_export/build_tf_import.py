import sys
import requests
import os
import logging
from python_terraform import *
import argparse

tf = Terraform()

# Set up Logging
logging.basicConfig(filename='build_tf_import.log', format='%(message)s', level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

# Parse Command line args
parser = argparse.ArgumentParser(description='Export O11y Synthetic Checks to Terraform resources')
parser.add_argument('--token', help='Splunk O11y Access Token (API)')
parser.add_argument('--realm', help='Splunk O11y Realm (example "us1")')
args = parser.parse_args()

o11y_key = args.token
realm    = args.realm

def get_resource( check_type ):
    if check_type == 'browser':
        return( "synthetics_create_browser_check_v2" )
    elif check_type == 'api':
        return( "synthetics_create_api_check_v2" )
    elif check_type == 'http':
        return( "synthetics_create_http_check_v2" )
    elif check_type == 'port':
        return( "synthetics_create_port_check_v2" )
    else:
        return( 'unknown' )

################################################################################
# Function: main()
################################################################################
def main():

    # Get all checks from O11y
    logging.info('Requesting Checks')
    o11y_headers_obj = { 'Content-Type': 'application/json; charset=utf-8', 'X-SF-TOKEN': o11y_key }
    r = requests.get('https://api.' + realm + '.signalfx.com/v2/synthetics/tests?perPage=2000', headers=o11y_headers_obj)
    r.raise_for_status()
    check_list_json = r.json()

    # for each check
    for check in check_list_json['tests']:

        # if check['id'] != 305480:
        #     continue

        res_type = get_resource( check['type'])
        res_name = check['type'] + '_' + str(check['id'])
        logging.info( check['name'] + ' (' + check['type'] + ') to resource "' + res_type + '.' + res_name + '"')
        filename = res_type + '.' + str(check['id']) + '.tf'

        # Build tf file for import
        f = open(filename, "w")
        res_type = get_resource( check['type'])
        f.write( 'resource "' + res_type + '" "' + res_name + '" {}\n')
        f.close()

        # Do import
        logging.info( '  Importing into Terraform state file')
        return_code, stdout, stderr = tf.import_cmd( res_type + '.' + res_name, str(check['id']), var={'access_token': o11y_key, 'realm': realm})
        if return_code > 1:  # 0 is OK, 1 is already in terraform
            logging.info( '   Return code: ' + str(return_code) + ' (' + stdout + ')')

        # Remove import file
        #os.remove( "import.tf" )

        # Get TF for resource into file           
        logging.info( '  Extracting and saving definition to file: "' + filename + '"')
        return_code, stdout, stderr = tf.state_cmd("show", res_type + '.' + res_name)
        if return_code > 1:  # 0 is OK, 1 is already in terraform
            logging.info( '  TF SHOW   "' + res_name + '" Return code: ' + str(return_code) + ' (' + stdout + ')')
        else:
            f = open( filename, "w")

            for line in stdout.splitlines():
                if 'id = "' in line:                      # skip ID line
                    continue
                if 'id                  = 0' in line:     # Weird http thing
                    continue
                f.write( line + '\n')

            f.close()

                 

    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()
        main()
    
