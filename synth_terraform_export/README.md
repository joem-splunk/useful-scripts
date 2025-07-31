# O11y Synthetics Terraform Export

The `build_tf_import.py` script exports all Synthetic checks in a o11y org to Terraform resource files

## Support

This script is provided "as-is" and is not offically supported by Splunk.

## Requirements

This script requires Python 3. You can optionally create a virtual environment:

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

```
usage: build_tf_import.py [-h] --token [API_TOKEN] --realm [O11Y_REALM]

Export a Splunk Observability Cloud Synthetics checks into Terraform resources
```

Here's an example:

```
python build_tf_import.py --token XXX --realm us1
```

This command will recursively export each individual synthetic check into a Terraform resource file. 
The files will be named `<tf_resource_type>.<check_id>.tf`.

Example: `synthetics_create_browser_check_v2.292775.tf`

## Important Notes

* The exporter may have trouble with certain, multi-line fields such as SOAP payloads or Javascript text
