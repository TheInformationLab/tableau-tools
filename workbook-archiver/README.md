# Tableau Workbook Exporter

A command-line tool to export all Tableau workbooks from a Tableau Server or Tableau Cloud site using the [Tableau Server Client (TSC) library](https://github.com/tableau/server-client-python).

This script is useful for archiving or migrating workbooks from one environment to another. It supports Personal Access Token (PAT) authentication and automatically downloads workbooks across all accessible sites.

---

## 🚀 Features

- Authenticates using Tableau Personal Access Tokens (PAT)
- Queries all accessible sites on a Tableau Server
- Downloads all workbooks from each site
- Organizes downloaded workbooks by site and project
- Sanitizes names to ensure safe filenames
- Compatible with both Tableau Server and Tableau Cloud

---

## 📦 Requirements

- Python 3.7+
- [tableauserverclient](https://pypi.org/project/tableauserverclient/)

Install dependencies using pip:

```bash
pip install tableauserverclient
```

---

## 🛠 Usage

```bash
python workbook_archiver.py <server> <pat_name> <pat_secret> <output_directory> [--initial-site <site_uri>]

```

### Arguments

- `<server>`: URL to your Tableau Server, e.g. `https://tableau.example.com/`
- `<pat_name>`: The name of your Personal Access Token
- `<pat_secret>`: The secret associated with the PAT
- `<output_directory>`: Local path where workbooks will be saved (e.g., `C:\Users\you\Downloads\Backup`)
- `<--initial-site>`: (Optional) Site URI to use for the initial sign-in (useful if you do not have access to the default site)

### Example

```bash
python workbook_archiver.py https://tableau.example.com my-token-name my-secret "C:\Archive"
```
### Example with --initial-site

```bash
python workbook_archiver.py https://tableau.example.com token-name token-secret "C:\Archive" --initial-site marketing

```

---

## 🗂 Output Structure

The output directory will be structured as follows:

```
<output_directory>/
├── SiteOne/
│   ├── projectID1~ProjectName/
│   │   ├── Workbook A.twbx
│   │   └── Workbook B.twbx
|   ├── projectID2~ProjectName/
│   │   ├── Workbook C.twbx
│   │   └── Workbook D.twbx
├── SiteTwo/
│   └── projectID3~ProjectName/
│       └── Workbook E.twbx
```

> Note: Project names are sanitized and prefixed with their project ID to avoid duplicates.

---

## 🔐 Authentication

This tool uses **Personal Access Tokens** (PAT) for authentication. You can generate a PAT from your Tableau user settings.

- You **must** have access to all the sites you intend to export workbooks from.
- If you do not have access to the "default" site, you **must** provide the site URI of a site you do have access to. The script will still proceed using the appropriate site URIs.

---

## ⚠️ Limitations

- Nested projects are not supported. Projects are uniquely identified using their ID and flattened into a single-level folder structure.
- Does not currently support workbook versioning or filtering by ownership/date.

---

## 🧩 Related Resources

- [Tableau REST API](https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref.htm)
- [Tableau Server Client Library](https://github.com/tableau/server-client-python)
