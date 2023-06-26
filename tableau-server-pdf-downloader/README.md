# Tableau Server/Cloud FullPDF Downloader Script

This Python scripts emulates the download 'fullpdf' functionality that is available in the original version of tabcmd.

While the newer version of tabcmd can download all views in a workbook as a PDF, it is currently unable to apply a filter to all views.

This script aims to offer a replacement for that missing functionality until Tableau developers build the option into the REST API.

## Usage

The script requires a number of input variables, which can be provided interactively at runtime, or in a JSON file, as described below. To choose between these two options, specify one of the following arguments when running the script:

Use the argument '-f (filename)' to provide a JSON file as input
If using a file, see the config-example.json file for an example of the required format.

Use the argument '-q' to be prompted with questions.
If running interactively, you will be prompted at the command line to input all the variables.

## Authentication

The script accepts authentication with both username/password or personal access token. Specify either 'password', or 'token' as your auth_method in the prompts or configuration file, including the relevant values as described below.

## How to run

Ensure you are using Python 3.7 or later.

If using a configuration file, run the script with:

    python /path/to/tableau_fullpdf_downloader.py -f /path/to/config.json, or

If you are not using a configuraiton file and want to be prompted for input, run the script with:

    python /path/to/tableau_fullpdf_downloader.py -q

## Example configuration files

Using PAT authentication:

    {
    "server_url": "https://your-tableau-server-url",
    "auth_method": "token",
    "token_name": "token_name",
    "token_value": "token_value",
    "site_name": "your-site-name",
    "project_name": "your-project-name",
    "workbook_name": "your-workbook-name",
    "pdf_orientation": "portrait",
    "output_filename": "your-output-filename.pdf",
    "output_path": "/your/output/path",
    "filter_field": "field-name",
    "filter_value": "field-value"
    }

Using username/password authentication:

    {
    "server_url": "https://your-tableau-server-url",
    "auth_method": "password",
    "username": "myusername",
    "password": "mypassword",
    "site_name": "your-site-name",
    "project_name": "your-project-name",
    "workbook_name": "your-workbook-name",
    "pdf_orientation": "portrait",
    "output_filename": "your-output-filename.pdf",
    "output_path": "/your/output/path",
    "filter_field": "field-name",
    "filter_value": "field-value"
    }
