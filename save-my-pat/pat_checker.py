"""Function to refresh PAT validity and check expiry on Tableau Cloud."""
import argparse
import json
from datetime import datetime
import logging
import requests

## Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logging.info("Beginning process, logging output to terminal")

def parse_arguments():
    """Function to parse module arguments."""
    # Parse arguments
    logging.info("Parsing arguments...")
    parser = argparse.ArgumentParser(
    description="Refresh expiration of PAT token and check validity duration."
    )
    parser.add_argument("server", help="Tableau server URL e.g. https://tableau.example.com/")
    parser.add_argument("site_uri", help="URI for the site, as seen in the address bar")
    parser.add_argument("token_name", help="Personal access token name")
    parser.add_argument("token_secret", help="Personal access token secret")
    parser.add_argument("-t", "--age_threshold",
        help="Number of days until expiry to start raising warnings")

    args = parser.parse_args()
    return args

def get_api_version(server_url):
    """Function to get API version in use on the provided server"""
    logging.info("Getting latest Tableau API version...")
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
    logging.info("API version to use: %s", str(api_version))
    return api_version

def parse_site_id(auth_response):
    """Function to parse site ID from authentication response."""
    # parse signin response
    try:
        site_id = auth_response['credentials']['site']['id']
    except NameError as exc:
        raise NameError("Site ID not found") from exc
    return site_id

def parse_user_id(auth_response):
    """Function to parse site ID from authentication response."""
    # parse signin response
    try:
        user_id = auth_response['credentials']['user']['id']
    except NameError as exc:
        raise NameError("User ID not found") from exc
    return user_id

def parse_x_tableau_auth(auth_response):
    """Function to parse authentication token from authentication response."""
    # parse signin response
    try:
        token = auth_response['credentials']['token']
    except NameError as exc:
        raise NameError("REST API authentication token not found") from exc
    return token

def get_auth_response(
    token_name,
    token_secret,
    server_url,
    site_uri,
    api_version
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
    logging.info("Sign in response code: %s", auth_resp.status_code)
    # test authentication response
    if auth_resp.status_code == 200:
        # parse response for site id and X-Tableau-Auth token
        logging.info("Authentication successful, parsing token...")
        r = json.loads(auth_resp.text)
        site_id = parse_site_id(r)
        logging.info("Site ID: %s", site_id)
        user_id = parse_user_id(r)
        logging.info("User ID: %s", user_id)
        tab_auth = parse_x_tableau_auth(r)
        return site_id, tab_auth, user_id
    raise ValueError("Sign in failed.",auth_resp.text)

def list_personal_access_tokens(
    server_url,
    api_version,
    site_id,
    user_id,
    auth_token
    ):
    """Function to list personal access tokens"""
    logging.info("Listing user's personal access tokens...")
    list_pat_endpoint = (
        server_url+"api/"+
        api_version+
        "/sites/"+
        site_id+
        "/users/"+
        user_id+
        "/personal-access-tokens"
        )
    auth_header = {
        "X-Tableau-Auth":auth_token,
        "accept":"application/json"
        }
    resp = requests.get(list_pat_endpoint, headers=auth_header, timeout=10)
    if resp.status_code == 200:
        tokens = json.loads(resp.text)["personalAccessTokens"]["personalAccessToken"]
        logging.info("%s personal access tokens found", str(len(tokens)))
        return tokens
    raise ValueError("List personal access tokens failed.", resp.text)

def get_token_expiry(token_list, token_name):
    """Function to check the expiry date of the used personal access token"""
    logging.info("Getting expiry date for token '%s'", token_name)
    for token in token_list:
        if token["tokenName"] == token_name:
            expiry = token["expiresAt"]
            expiry_date = datetime.strptime(expiry, "%Y-%m-%dT%H:%M:%SZ")
            logging.info("Token %s expires %s", token_name, str(expiry_date))
            return expiry_date
    return None

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
        logging.info("Sign out status: %s", resp.status_code)
        return resp.text, resp.status_code
    raise ValueError("Sign out failed.")

def main():
    """Main process for the token checking."""

    # Parse arguments
    args = parse_arguments()

    server = args.server
    if not server.endswith("/"):
        server += "/"
    site_uri = args.site_uri
    token_name = args.token_name
    token_secret = args.token_secret
    if not args.age_threshold:
        age_threshold = 30
    else:
        age_threshold = int(args.age_threshold)
    api_version = get_api_version(server)

    logging.info("Signing into server %s using supplied PAT.", server)
    site_id, auth_token, user_id = get_auth_response(
        token_name,
        token_secret,
        server,
        site_uri,
        api_version
        )

    if "online.tableau.com" in server:
        logging.info("Tableau Cloud detected, checking token expiry...")

        # get expiry date of the token used for this session
        expiry = get_token_expiry(
            list_personal_access_tokens(
                server,
                api_version,
                site_id,
                user_id,
                auth_token
                ),
            token_name)

        # get difference between expiry and now in days
        diff = (expiry - datetime.now()).days

        if diff < age_threshold:
            # Raise a warning about upcoming expiry
            logging.warning(
                "Tableau personal access token expiry for %s will expire %s days from now.",
                token_name,
                str(diff)
                )
            logging.warning("Expires at: %s", str(expiry))
            logging.warning(
                "Consider updating the personal access token in Tableau Server for '%s' on %s.",
                token_name,
                server
                )
        else:
            logging.info(
            "Token expiry is more than %s days from now, skipping warning. Days to expiry: %s",
            str(age_threshold),
            str(diff)
            )
    else:
        logging.info("Tableau Server detected, skipping token expiry check")

    logging.info("Clearing sign in session.")
    body, status_code = sign_out(
        server,
        api_version,
        auth_token
        )
    if status_code == 204:
        logging.info("Sign out successful.")
    else:
        logging.info("Sign out unsuccessful. Status code: %s, %s",
                     status_code,
                     body)

    logging.info("Token expiry successfully reset for %s",token_name)

if __name__ == "__main__":
    main()
