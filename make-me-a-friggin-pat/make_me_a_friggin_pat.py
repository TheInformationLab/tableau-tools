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
        # Normalize base URL and create a requests session
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
        self.verify_ssl = verify_ssl
        # Storage for RSA key components
        self.key_id = None
        self.n = None
        self.e = None

    def _headers(self, xsrf_token=None):
        """
        Build the common headers for Vizportal JSON calls.
        Include X-XSRF-TOKEN header if provided.
        """
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Accept': 'application/json, text/plain, */*',
            'Cache-Control': 'no-cache',
        }
        if xsrf_token:
            headers['X-XSRF-TOKEN'] = xsrf_token
        return headers

    def generate_public_key(self):
        """
        Retrieve the RSA public key from Vizportal.
        Stores keyId, modulus (n) and exponent (e).
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
        # key could be returned as hex string or integer
        self.n = result["key"]["n"]
        self.e = result["key"]["e"]
        return self.key_id, self.n, self.e

    def encrypt_password(self, plaintext_password):
        """
        Encrypt the plaintext password using the fetched RSA public key.
        Handles cases where n/e are hex strings, ints, or missing.
        Returns the hex-encoded cipher text.
        """
        # Ensure public key is available
        if self.n is None or self.e is None:
            raise RuntimeError("Public key not initialized. Call generate_public_key() first.")

        # Parse modulus and exponent if needed
        if isinstance(self.n, str):
            modulus = int(self.n, 16)
        else:
            modulus = int(self.n)

        if isinstance(self.e, str):
            exponent = int(self.e, 16)
        else:
            exponent = int(self.e)

        # Construct RSA key and encrypt
        pubkey = RSA.construct((modulus, exponent))
        cipher = PKCS1_v1_5.new(pubkey)
        encrypted_bytes = cipher.encrypt(plaintext_password.encode('utf-8'))
        return binascii.b2a_hex(encrypted_bytes).decode('ascii')

    def login(self, username, plaintext_password):
        """
        Perform the login sequence:
        1) Fetch or refresh public key
        2) Encrypt password
        3) POST to /login
        4) Extract workgroup_session_id & XSRF-TOKEN
        """
        # Always regenerate key if missing or incomplete
        if self.key_id is None or self.n is None or self.e is None:
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

        # Cookies are set HttpOnly; retrieve from session
        wg = self.session.cookies.get("workgroup_session_id")
        xsrf = self.session.cookies.get("XSRF-TOKEN")
        if not wg or not xsrf:
            raise RuntimeError("Login succeeded but tokens not found in cookies")

        return wg, xsrf

    def create_personal_access_token(self, client_id):
        """
        Create a PAT named client_id. Returns the refreshToken.
        Requires that login() has already been called.
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
    Entry point for CLI usage.
    Parse arguments, authenticate, print tokens, and optionally create a PAT.
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

    # Initialize auth helper and log in
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
