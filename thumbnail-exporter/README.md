# Tableau Thumbnail Exporter

A script to export workbook thumbnail preview images from a Tableau Server or Tableau Cloud site using the [Tableau Server Client (TSC) library](https://github.com/tableau/server-client-python) and the Tableau REST API.

---

## Features

- Exports PNG thumbnail images for all workbooks on a site
- Authenticates using Tableau Personal Access Tokens (PAT)
- Compatible with both Tableau Server and Tableau Cloud

---

## Requirements

- Python 3.7+
- [tableauserverclient](https://pypi.org/project/tableauserverclient/)
- [requests](https://pypi.org/project/requests/)

Install dependencies using pip:

```bash
pip install tableauserverclient requests
```

---

## Usage

This script uses constants defined at the top of the file for configuration. Open `get_thumbnails_standalone.py` and update the following values before running:

```python
# Two separate PATs are required (one for TSC, one for REST API calls)
TSC_TOKEN_NAME = "your-token-name-here"
TSC_TOKEN_SECRET = "your-token-secret-here"
API_TOKEN_NAME = "your-token-name-here"
API_TOKEN_SECRET = "your-token-secret-here"

OUTPUT_FILEPATH = "C:\\Users\\username\\Downloads\\thumbnails\\"
SERVER_URL = "https://tableauserver.example.com"
SITE_URI = '""'  # use '""' for the default site, or the site URI e.g. "my-site"
```

Then run the script:

```bash
python get_thumbnails_standalone.py
```

---

## Authentication

This script requires **two Personal Access Tokens** because it maintains two parallel sessions: one via the TSC library to query workbook metadata, and another via direct REST API calls to download the preview images.

You can generate PATs from your Tableau user settings.

---

## Related Resources

- [Tableau REST API](https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref.htm)
- [Tableau Server Client Library](https://github.com/tableau/server-client-python)
