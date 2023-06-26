# Import necessary libraries
import argparse
import getpass
import json
import os
import sys
import tableauserverclient as TSC
from PyPDF2 import PdfMerger, PdfReader

# Function to prompt user for required information


def prompt_user():
    data = {}
    # Ask user for server URL
    data["server_url"] = input("Please enter server URL: ")
    # Ask user for username
    data["username"] = input("Please enter your username: ")
    # Ask user for password (password will be hidden)
    data["password"] = getpass.getpass("Please enter your password: ")
    # Ask user for site name
    data["site_name"] = input("Please enter the site name: ")
    # Ask user for project name
    data["project_name"] = input("Please enter the project name: ")
    # Ask user for workbook name
    data["workbook_name"] = input("Please enter the workbook name: ")
    # Ask user for PDF orientation
    data["pdf_orientation"] = input(
        "Please enter the PDF orientation ('portrait' or 'landscape'): ")
    # Ask user for output path
    data["output_path"] = input("Please enter the output path: ")
    # Ask user for output filename
    data["output_filename"] = input("Please enter the output filename: ")
    # Ask user for filter field
    data["filter_field"] = input(
        "Please enter the field name to apply the filter on: ")
    # Ask user for filter value
    data["filter_value"] = input("Please enter the filter value: ")
    return data

# Function to parse a JSON file


def parse_json(file_path):
    with open(file_path, 'r') as json_file:  # Open JSON file
        data = json.load(json_file)  # Load data from JSON file
    return data

# Main function to run the program


def main():
    parser = argparse.ArgumentParser()  # Initialize argument parser
    # Add command-line argument options
    parser.add_argument('-q', '--question', action='store_true',
                        help='Prompt user to input required information')
    parser.add_argument('-f', '--file', type=str,
                        help='Path to json file containing required information')
    args = parser.parse_args()  # Parse command-line arguments

    # Check which option was selected by the user
    if '-q' in sys.argv or '--question' in sys.argv or len(sys.argv) == 1:
        data = prompt_user()  # If user selected "-q", prompt user for required information
    elif '-f' in sys.argv or '--file' in sys.argv:
        # If user selected "-f", load required information from JSON file
        data = parse_json(args.file)
    else:
        # Display error if no recognized option was selected
        parser.error(
            "No recognized arguments provided. Use -q to input information or -f to use a json file.")

    # Assign variables to data from user or JSON file
    server_url = data["server_url"]
    username = data["username"]
    password = data["password"]
    site_name = data["site_name"]
    project_name = data["project_name"]
    workbook_name = data["workbook_name"]
    pdf_orientation = data["pdf_orientation"]
    output_path = data["output_path"]
    output_filename = data["output_filename"]
    filter_field = data["filter_field"]
    filter_value = data["filter_value"]

    # Initialize Tableau authentication and server
    tableau_auth = TSC.TableauAuth(username, password, site_name)
    server = TSC.Server(server_url, use_server_version=True)

    # Set PDF request options
    pdf_request_options = TSC.PDFRequestOptions(orientation=pdf_orientation)
    pdf_request_options.vf(filter_field, filter_value)  # Apply filter

    # Begin server authentication
    with server.auth.sign_in(tableau_auth):
        all_projects, _ = server.projects.get()  # Get all projects
        # Get project specified by user or JSON file
        project = next(
            (project for project in all_projects if project.name == project_name), None)

        if not project:
            # If specified project not found, display error
            print(f"No project named '{project_name}' found.")
            return

        # Create request options for workbook
        req_option_workbook = TSC.RequestOptions()
        req_option_workbook.filter.add(TSC.Filter(TSC.RequestOptions.Field.ProjectName,
                                                  TSC.RequestOptions.Operator.Equals,
                                                  project_name))  # Add filter for project name

        all_workbooks, _ = server.workbooks.get(
            req_option_workbook)  # Get all workbooks
        for wb in all_workbooks:
            # If workbook name matches the one specified by user or JSON file
            if wb.name.lower() == workbook_name.lower():
                all_views, _ = server.views.get()  # Get all views
                with PdfMerger() as merger:  # Begin PDF merge
                    for view in all_views:
                        if view.workbook_id == wb.id:  # If view belongs to the specified workbook
                            # Populate PDF for the view
                            server.views.populate_pdf(
                                view, pdf_request_options)
                            # Set path for the PDF
                            pdf_path = os.path.join(
                                output_path, f"{view.name}.pdf")
                            with open(pdf_path, "wb") as f:  # Open PDF file
                                f.write(view.pdf)  # Write PDF data to file
                            merger.append(pdf_path)  # Append PDF to the merger
                            # Deletes the individual PDF file after merging
                            os.remove(pdf_path)
                    # Write merged PDF file to specified output path
                    merger.write(os.path.join(output_path, output_filename))


# Call the main function when the script is run
if __name__ == '__main__':
    main()
