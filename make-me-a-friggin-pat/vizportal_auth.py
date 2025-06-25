#!/usr/bin/env python3
"""A command-line tool to authenticate to Tableau Vizportal and return session tokens."""
import argparse
import binascii
import requests
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5


class VizportalAuth:
    """A class to handle authentication to Tableau Vizportal using the web API."""
    def __init__(self, server_url, verify_ssl=True):
        """
        :param server_url: Base URL of your Tableau Server, e.g. https://tableau.example.com
        :param verify_ssl:  False to disable SSL verification
        """
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
        self.verify_ssl = verify_ssl
        self.key_id = None
        self.n = None
        self.e = None

    def _headers(self, xsrf_token=None):
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
        Calls /generatePublicKey and stores keyId, modulus (n) and exponent (e).
        """
        url = f"{self.server_url}/vizportal/api/web/v1/generatePublicKey"
        payload = { "method": "generatePublicKey", "params": {} }
        resp = self.session.post(url, json=payload,
                                 headers=self._headers(), verify=self.verify_ssl)
        resp.raise_for_status()
        result = resp.json()["result"]
        self.key_id = result["keyId"]
        self.n = result["key"]["n"]
        self.e = result["key"]["e"]
        return self.key_id, self.n, self.e

    def encrypt_password(self, plaintext_password):
        """
        Encrypts the given plaintext password using the public key just fetched.
        Returns a hex-encoded cipher.
        """
        if self.n is None or self.e is None:
            raise ValueError("Public key not generated. Call generate_public_key() first.")
        # Python3: use int() instead of long()
        modulus = int(self.n, 16)
        exponent = int(self.e, 16)
        pubkey = RSA.construct((modulus, exponent))
        cipher = PKCS1_v1_5.new(pubkey)
        encrypted_bytes = cipher.encrypt(plaintext_password.encode('utf-8'))
        # hexlify for the API
        return binascii.b2a_hex(encrypted_bytes).decode('ascii')

    def login(self, username, plaintext_password):
        """
        Performs the full login dance and returns (workgroup_session_id, xsrf_token).
        """
        # Step 1: get or refresh public key
        if not hasattr(self, 'key_id'):
            self.generate_public_key()

        # Step 2: encrypt the password
        encrypted_hex = self.encrypt_password(plaintext_password)

        # Step 3: call login
        url = f"{self.server_url}/vizportal/api/web/v1/login"
        payload = {
            "method": "login",
            "params": {
                "username": username,
                "encryptedPassword": encrypted_hex,
                "keyId": self.key_id
            }
        }
        resp = self.session.post(url, json=payload,
                                 headers=self._headers(), verify=self.verify_ssl)
        resp.raise_for_status()

        # Step 4: extract cookies from the session
        wg = self.session.cookies.get("workgroup_session_id")
        xsrf = self.session.cookies.get("XSRF-TOKEN")
        if not wg or not xsrf:
            raise RuntimeError("Login succeeded but tokens not found in cookies")

        return wg, xsrf

def main():
    """Main function to handle command line arguments and perform authentication."""
    parser = argparse.ArgumentParser(
        description="Authenticate to Tableau Vizportal and return session tokens"
    )
    parser.add_argument("server", help="e.g. https://tableau.example.com")
    parser.add_argument("username")
    parser.add_argument("password")
    parser.add_argument("--no-verify", action="store_true",
                        help="Disable SSL certificate verification")
    args = parser.parse_args()

    auth = VizportalAuth(args.server, verify_ssl=not args.no_verify)
    wg_id, xsrf = auth.login(args.username, args.password)

    print("workgroup_session_id:", wg_id)
    print("XSRF-TOKEN:", xsrf)

if __name__ == "__main__":
    main()
