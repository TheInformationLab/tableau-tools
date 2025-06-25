#!/usr/bin/env python3
"""
A command-line tool to authenticate to Tableau Vizportal and optionally 
create a Personal Access Token (PAT).
"""

import argparse           # parse command-line arguments
import binascii           # hex encoding utilities
import requests           # HTTP client
from Crypto.PublicKey import RSA           # for RSA public key handling
from Crypto.Cipher import PKCS1_v1_5       # for PKCS#1 v1.5 encryption

class VizportalAuth:
    """
    Encapsulates the Vizportal authentication flow:
    1. Fetch RSA public key
    2. Encrypt user password
    3. Log in to get session cookies
    4. (Optionally) create a PAT
    """
    def __init__(self, server_url, verify_ssl=True):
        # Normalize base URL (remove trailing slash) and create a requests.Session
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
        self.verify_ssl = verify_ssl
        self.key_id = None
        self.n = None
        self.e = None

    def _headers(self, xsrf_token=None):
        """
        Build the common headers for Vizportal JSON calls.
        If an XSRF token is provided, include it.
        """
        h = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Accept': 'application/json, text/plain, */*',
            'Cache-Control': 'no-cache',
        }
        if xsrf_token:
            h['X-XSRF-TOKEN'] = xsrf_token
        return h

    def generate_public_key(self):
        """
        Step 1: POST to /generatePublicKey to retrieve the RSA modulus & exponent.
        Stores keyId, n (modulus) and e (exponent) for later encryption.
        """
        url = f"{self.server_url}/vizportal/api/web/v1/generatePublicKey"
        payload = {"method": "generatePublicKey", "params": {}}
        resp = self.session.post(
            url,
            json=payload,
            headers=self._headers(),
            verify=self.verify_ssl
        )
        resp.raise_for_status()

        result = resp.json()["result"]
        self.key_id = result["keyId"]
        self.n = result["key"]["n"]
        self.e = result["key"]["e"]
        return self.key_id, self.n, self.e

    def encrypt_password(self, plaintext_password):
        """
        Step 2: Encrypt the plaintext password using the fetched RSA public key.
        Returns the hex-encoded cipher text required by Vizportal.
        """
        # Convert hex strings to integers
        modulus = int(self.n, 16)
        exponent = int(self.e, 16)
        pubkey = RSA.construct((modulus, exponent))
        cipher = PKCS1_v1_5.new(pubkey)

        # Encrypt and hex-encode
        encrypted_bytes = cipher.encrypt(plaintext_password.encode('utf-8'))
        return binascii.b2a_hex(encrypted_bytes).decode('ascii')

    def login(self, username, plaintext_password):
        """
        Step 3: Perform the login dance:
        - Ensure we have a public key (generate if needed)
        - Encrypt the password
        - POST credentials to /login
        - Extract workgroup_session_id & XSRF-TOKEN from cookies
        Returns (workgroup_session_id, XSRF-TOKEN)
        """
        if not hasattr(self, 'key_id'):
            self.generate_public_key()

        encrypted_hex = self.encrypt_password(plaintext_password)
        url = f"{self.server_url}/vizportal/api/web/v1/login"
        payload = {
            "method": "login",
            "params": {
                "username": username,
                "encryptedPassword": encrypted_hex,
                "keyId": self.key_id
            }
        }
        resp = self.session.post(
            url,
            json=payload,
            headers=self._headers(),
            verify=self.verify_ssl
        )
        resp.raise_for_status()

        # These cookies are set HttpOnly; requests.Session will capture them
        wg = self.session.cookies.get("workgroup_session_id")
        xsrf = self.session.cookies.get("XSRF-TOKEN")
        if not wg or not xsrf:
            raise RuntimeError("Login succeeded but tokens not found in cookies")

        return wg, xsrf

    def create_personal_access_token(self, client_id):
        """
        Step 4: Create a Personal Access Token (PAT) named client_id.
        Requires a prior successful login (to supply XSRF-TOKEN).
        Returns the refreshToken string.
        """
        xsrf = self.session.cookies.get("XSRF-TOKEN")
        if not xsrf:
            raise RuntimeError("Missing XSRF-TOKEN; please login first")

        url = f"{self.server_url}/vizportal/api/web/v1/createPersonalAccessToken"
        payload = {
            "method": "createPersonalAccessToken",
            "params": {"clientId": client_id}
        }
        resp = self.session.post(
            url,
            json=payload,
            headers=self._headers(xsrf_token=xsrf),
            verify=self.verify_ssl
        )
        resp.raise_for_status()

        result = resp.json().get("result", {})
        token = result.get("refreshToken")
        if not token:
            raise RuntimeError(f"Unexpected response: {resp.text}")

        return token

def main():
    """
    Command-line entrypoint:
    - Parse arguments
    - Login and print session tokens
    - Optionally create a PAT and print it
    """
    parser = argparse.ArgumentParser(
        description="Authenticate to Tableau Vizportal and (optionally) create a PAT"
    )
    parser.add_argument("server", help="e.g. https://tableau.example.com")
    parser.add_argument("username", help="Tableau username")
    parser.add_argument("password", help="Tableau password")
    parser.add_argument(
        "--pat-name",
        help="If provided, name of the Personal Access Token to create"
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Disable SSL certificate verification (not recommended)"
    )
    args = parser.parse_args()

    # Initialize and login
    auth = VizportalAuth(args.server, verify_ssl=not args.no_verify)
    wg_id, xsrf = auth.login(args.username, args.password)
    print("workgroup_session_id:", wg_id)
    print("XSRF-TOKEN:", xsrf)

    # Create PAT if requested
    if args.pat_name:
        pat = auth.create_personal_access_token(args.pat_name)
        print("Personal Access Token (refreshToken):", pat)

if __name__ == "__main__":
    main()
