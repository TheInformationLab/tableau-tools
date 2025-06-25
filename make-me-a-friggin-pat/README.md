# Tableau Vizportal Auth Helper

A simple Python CLI to authenticate against Tableau’s **undocumented** Vizportal API and (optionally) create a Personal Access Token (PAT).

## Why this is useful

- Automate tasks that require direct calls to Vizportal endpoints:
  - Creating PATs
  - Other internal admin operations not exposed in the official REST API
- Integrate with existing Python automation or CI/CD pipelines.

## Features

- **Encrypted-password login**  
  Fetches the RSA public key, encrypts your Tableau password, and logs in to obtain session cookies.
- **PAT creation**  
  Create a named Personal Access Token via Vizportal for later use with the REST API.
- **SSL verification toggle**  
  Disable SSL certificate checks for self-signed Tableau Server installs.

## Requirements

- Python 3.7+
- A **local** Tableau Server user account (username/password).
  - **Note**: SAML‐only users must have a local password created.
  - **Tableau Cloud** (hosted SaaS) does **not** support this login flow.
- The following Python packages:
  ```txt
  requests
  pycryptodome
  ```

## Installation

1. Clone this repository:

```bash
git clone https://github.com/TheInformationLab/tableau-tools.git
cd tableau-tools
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Authenticate and print session tokens
python vizportal_auth.py https://tableau.example.com alice MyP@ssw0rd

# Authenticate and create a PAT named "automation-bot"
python vizportal_auth.py https://tableau.example.com alice MyP@ssw0rd --pat-name automation-bot
```

## Output

```bash
workgroup_session_id: <SESSION_ID>
XSRF-TOKEN: <XSRF_TOKEN>
Personal Access Token: <PAT_TOKEN>   # if --pat-name used
```

Store the PAT securely; it can be used with the Tableau REST API /api/{version}/auth/signin flow.

## Limitations & Caveats

- Server-only: Does not work against Tableau Cloud (SaaS) sites.
- Requires local credentials: In SSO/SAML deployments, ensure a local machine account exists.
- Session cookies: workgroup_session_id is HttpOnly and session-scoped—automated extraction may need browser automation (Selenium, Playwright) if you wish to reuse an existing browser login.

## Best Practices

- Least-privilege account: Create a dedicated service user with only the necessary permissions.
- Secure storage: Never commit your password or PAT to source control — use environment variables or vaults.
- Rotate tokens: Regularly delete and recreate PATs to minimise risk.
- SSL verification: Keep --no-verify for testing only; enable SSL checks in production.

Note: This tool leverages an unsupported Tableau “web client” API. Behaviour may change in future Tableau Server releases.

```

```
