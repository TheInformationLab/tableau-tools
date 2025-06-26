# Tableau Workbook Exporter

A command-line tool to export all Tableau workbooks from a Tableau Server or Tableau Cloud site using the [Tableau Server Client (TSC) library](https://github.com/tableau/server-client-python).

This script is useful for archiving or migrating workbooks from one environment to another. It supports Personal Access Token (PAT) authentication and automatically downloads workbooks across all accessible sites (for Server) or a specified site (for Cloud).

---

## 🚀 Features

- Authenticates using Tableau Personal Access Tokens (PAT)
- Detects Tableau Server vs. Tableau Cloud
- Queries all accessible sites (for Tableau Server only)
- Requires a site URI for Tableau Cloud
- Reconstructs **nested project folder hierarchy** for clean archiving
- Downloads all workbooks from each site
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

> **Tableau Cloud Users**: You must specify `--initial-site` as listing all sites is not supported in Tableau Cloud. Only the specified site will be exported.


```bash
python workbook_archiver.py <server> <pat_name> <pat_secret> <output_directory> [--initial-site <site_uri>]

```

### Arguments

- `<server>`: URL to your Tableau Server, e.g. `https://tableau.example.com/`
- `<pat_name>`: The name of your Personal Access Token
- `<pat_secret>`: The secret associated with the PAT
- `<output_directory>`: Local path where workbooks will be saved (e.g., `C:\Users\you\Downloads\Backup`)
- `<--initial-site>`: *(Required for Tableau Cloud. Optional for Tableau Server)* Site URI to use for the initial sign-in (useful if you do not have access to the default site).

### Example

```bash
python workbook_archiver.py https://tableau.example.com/ my-token-name my-secret "C:\Archive"
```
### Example with --initial-site

```bash
python workbook_archiver.py https://10az.online.tableau.com/ token-name token-secret "C:\Archive" --initial-site marketing

```

---

## 🗂 Output Structure

The output directory will be structured by site, and then by the **full nested path** of the project:

```
<output_directory>/
├── SiteOne/
│   └── Department/
│       └── Finance/
│            └── Quarterly Reports/
│               ├── Workbook A.twbx
│               └── Workbook B.twbx
├── SiteTwo/
│   └── Department/
│       └── Finance/
│            └── Quarterly Reports/
│               ├── Workbook A.twbx
│               └── Workbook B.twbx
```

> Note: Project and workbook names are sanitized to remove illegal filesystem characters.

---

## ☁️ Tableau Cloud Notice

If using **Tableau Cloud** (`*.online.tableau.com`), the script:
- Skips querying all sites (which is not permitted by the API)
- Requires `--initial-site` to be explicitly provided
- Exports only from the specified site

---

## 🔐 Authentication

This tool uses **Personal Access Tokens** (PAT) for authentication. You can generate a PAT from your Tableau user settings.

- You **must** have access to all the sites you intend to export workbooks from.
- If you do not have access to the "default" site, you **must** provide the site URI of a site you do have access to. The script will still proceed using the appropriate site URIs.

---

## ⚠️ Limitations

- Workbooks are downloaded in their current published state.
- Does not support filtering workbooks by tags, dates, or owner.

---

## 🧩 Related Resources

- [Tableau REST API](https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref.htm)
- [Tableau Server Client Library](https://github.com/tableau/server-client-python)
