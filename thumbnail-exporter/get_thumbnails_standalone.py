"""Module for exporting thumbnails images from a Tableau Server or Cloud site."""

import json
import requests
import tableauserverclient as TSC

## You need to personal access tokens for this script.
## This is because the script requires two sessions to be open in parallel

## One is used for the Tableau Server Client
TSC_TOKEN_NAME = "your-token-name-here"
TSC_TOKEN_SECRET= "your-token-secret-here"
## The other for direct API calls
API_TOKEN_NAME = "your-token-name-here"
API_TOKEN_SECRET = "your-token-secret-here"

# you need to use double backslashes in the path for it to work
OUTPUT_FILEPATH = "C:\\Users\\username\\Downloads\\thumbnails\\"

SERVER_URL = "https://tableau.company.com"
# use this for the default site
# otherwise enter the site as it appears in the URL e.g. til2 for The Information Lab site
SITE_URI = '""'

TABLEAU_AUTH = TSC.PersonalAccessTokenAuth(TSC_TOKEN_NAME, TSC_TOKEN_SECRET, site_id=SITE_URI)
SERVER = TSC.Server(SERVER_URL, use_server_version=True)

# Authentication functions
def get_api_version(server_url:str):
    """Function to get latest API version in use on the provided server"""
    header = {
        "accept":"application/json"
        }
    server_info = json.loads(
        requests.get(
            server_url+"api/2.4/serverinfo",
            headers=header,
            timeout=5)
        .text
        )
    api_version = server_info["serverInfo"]["restApiVersion"]
    return api_version

def get_auth_response(
    token_name:str,
    token_secret:str,
    server_url:str,
    site_uri:str,
    api_version:str
    ):
    """Function to get authentication token for subsequent API calls"""
    # set data types for request bodies
    header = {
        "Content-Type": "application/xml",
        "Accept":"application/json"
        }
    # get sign in details
    # sign in url
    signin_endpoint = (
        server_url+"api/"+
        api_version+
        "/auth/signin"
        )
    # body including credentials
    # this is xml as only xml example is provided in the Tableau docs
    signin_body = (
        '<tsRequest><credentials personalAccessTokenName="'
        +token_name+
        '" personalAccessTokenSecret="'
        +token_secret+
        '"><site contentUrl="'
        +site_uri+
        '" /></credentials></tsRequest>')
    # send signin request
    auth_resp = requests.post(
        signin_endpoint,
        headers=header,
        data=signin_body,
        timeout=5
        )
    print("Sign in response code: ",auth_resp.status_code)
    # test authentication response
    if auth_resp.status_code == 200:
        # parse response for site id and X-Tableau-Auth token
        r = json.loads(auth_resp.text)
        site_id = parse_site_id(r)
        tab_auth = parse_x_tableau_auth(r)
        return site_id, tab_auth
    raise ValueError("Sign in failed.",auth_resp.status_code, ":", auth_resp.text)

def parse_site_id(auth_response):
    """Function to parse site ID from authentication response."""
    # parse signin response
    try:
        site_id = auth_response['credentials']['site']['id']
    except NameError as exc:
        raise NameError("Site ID not found") from exc
    return site_id

def parse_x_tableau_auth(auth_response):
    """Function to parse authentication token from authentication response."""
    # parse signin response
    try:
        token = auth_response['credentials']['token']
    except NameError as exc:
        raise NameError("REST API authentication token not found") from exc
    return token

def sign_out(
    server_url,
    api_version,
    auth_token
    ):
    """Function to sign out from server"""
    sign_out_endpoint = (
        server_url+"api/"+
        api_version+
        "/auth/signout"
        )
    auth_header = {"X-Tableau-Auth":auth_token}
    resp = requests.post(sign_out_endpoint,headers=auth_header,timeout=10)
    if resp.status_code == 204:
        print(resp.text)
    else:
        raise ValueError("Sign out failed.")

## Manual sign in ##
API_VERSION = get_api_version(SERVER_URL)
SITE_ID, AUTH_TOKEN = get_auth_response(
                        API_TOKEN_NAME,
                        API_TOKEN_SECRET,
                        SERVER_URL,
                        SITE_URI,
                        API_VERSION
                        )

# function to get all workbooks for the site
def query_workbook_ids(server, tableau_auth):
    """Function to get all workbooks on the site""" 
    _wb_list = []
    with server.auth.sign_in(tableau_auth):
        for _wb in TSC.Pager(server.workbooks):
            _d = {
                "id":_wb.id,
                "name":_wb.name,
                "project_name":_wb.project_name,
                "content_url":_wb.content_url
                }
            print(_wb)
            _wb_list.append(_d)
    return _wb_list

# function to download thumbnails for the provided workbook
def download_thumbnails(
                        workbook_id:str,
                        workbook_name:str,
                        output_path:str
                        ):
    """Function to download a workbook thumbnail"""
    query_endpoint = (
        f"{SERVER_URL}/api/{API_VERSION}/sites/{SITE_ID}/workbooks/{workbook_id}/previewImage"
        )
    auth_header = {"X-Tableau-Auth":AUTH_TOKEN}
    image = requests.get(query_endpoint,
                         headers=auth_header,
                         timeout=60
                         )
    image_name = workbook_name+".png"
    fullpath = output_path+image_name
    with open(fullpath, 'wb') as f:
        f.write(image.content)

## get all the workbooks on the site
workbooks = query_workbook_ids(SERVER,TABLEAU_AUTH)

## download the thumbnail for each workbook
for wb in workbooks:
    wb_id = wb['id']
    wb_name = wb['content_url']
    download_thumbnails(wb_id,wb_name, OUTPUT_FILEPATH)
