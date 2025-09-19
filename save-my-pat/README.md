# Personal Access Token Monitoring

A command-line tool to refresh Personal Access Token validity on a Tableau Server or Tableau Cloud site.

Personal access tokens automatically expire if not used within 14 days. This script is useful for keeping infrequently used tokens available for automated processes by using the token to sign into and out of Tableau.

Additionally, for Tableau Cloud the script will check if the token is due to expire within the supplied time frame and raise a warning if the token will expire soon.

---

## 🚀 Features

- Authenticates using Tableau Personal Access Tokens (PAT)
- Detects Tableau Server vs. Tableau Cloud
- Checks token validity on Tableau Cloud. This is not supported by the Tableau Server REST API.
- Requires a site URI for authentication
- Compatible with both Tableau Server and Tableau Cloud

---

## 📦 Requirements

- Python 3.7+
- [requests](https://pypi.org/project/requests/)

Install dependencies using pip:

```bash
pip install requests
```

---

## 🛠 Usage

> **Tableau Cloud Users**: You must specify `--initial-site` as listing all sites is not supported in Tableau Cloud. Only the specified site will be exported.


```bash
python pat_checker.py <server> <site_uri> <token_name> <token_secret> <age_threshold>

```

### Arguments

- `<server>`: URL to your Tableau Server, e.g. `https://tableau.example.com/`
- `<site_uri>`: URI of the site to sign into, as it appears in the address bar
- `<token_name>`: The name of your Personal Access Token
- `<token_secret>`: The secret associated with the PAT
- `<age_threshold>`: Time in days before expiry to start triggering warnings

### Example

```bash
python pat_checker.py https://tableau.example.com/ my-site my-token-name my-secret-value 30
```

---


## 🧩 Related Resources

- [Tableau Personal Access Tokens](https://help.tableau.com/current/server/en-us/security_personal_access_tokens.htm)
- [Tableau REST API](https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref.htm)
