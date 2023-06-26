import argparse
import getpass
import json
import os
import sys
import tableauserverclient as TSC
from PyPDF2 import PdfMerger, PdfReader

def prompt_user():
    data = {}
    data["server_url"] = input("Please enter server URL: ")
    data["username"] = input("Please enter your username: ")
    data["password"] = getpass.getpass("Please enter your password: ")  # Hides password
    data["site_name"] = input("Please enter the site name: ")
    data["project_name"] = input("Please enter the project name: ")
    data["workbook_name"] = input("Please enter the workbook name: ")
    data["pdf_orientation"] = input("Please enter the PDF orientation ('portrait' or 'landscape'): ")
    data["output_path"] = input("Please enter the output path: ")
    data["output_filename"] = input("Please enter the output filename: ")
    data["filter_field"] = input("Please enter the field name to apply the filter on: ")
    data["filter_value"] = input("Please enter the filter value: ")
    return data

def parse_json(file_path):
    with open(file_path, 'r') as json_file:
        data = json.load(json_file)
    return data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-q', '--question', action='store_true', help='Prompt user to input required information')
    parser.add_argument('-f', '--file', type=str, help='Path to json file containing required information')
    args = parser.parse_args()

    if '-q' in sys.argv or '--question' in sys.argv or len(sys.argv) == 1:
        data = prompt_user()
    elif '-f' in sys.argv or '--file' in sys.argv:
        data = parse_json(args.file)
    else:
        parser.error("No recognized arguments provided. Use -q to input information or -f to use a json file.")

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

    tableau_auth = TSC.TableauAuth(username, password, site_name)
    server = TSC.Server(server_url, use_server_version=True)

    pdf_request_options = TSC.PDFRequestOptions(orientation=pdf_orientation)
    pdf_request_options.vf(filter_field, filter_value)  # vf is short for vizql filter
    
    with server.auth.sign_in(tableau_auth):
        all_projects, _ = server.projects.get()
        project = next((project for project in all_projects if project.name == project_name), None)

        if not project:
            print(f"No project named '{project_name}' found.")
            return
        
        req_option_workbook = TSC.RequestOptions()
        req_option_workbook.filter.add(TSC.Filter(TSC.RequestOptions.Field.ProjectName,
                                                  TSC.RequestOptions.Operator.Equals,
                                                  project_name))
        
        all_workbooks, _ = server.workbooks.get(req_option_workbook)
        for wb in all_workbooks:
            if wb.name.lower() == workbook_name.lower():
                all_views, _ = server.views.get()
                with PdfMerger() as merger:
                    for view in all_views:
                        if view.workbook_id == wb.id:
                            server.views.populate_pdf(view, pdf_request_options)
                            pdf_path = os.path.join(output_path, f"{view.name}.pdf")
                            with open(pdf_path, "wb") as f:
                                f.write(view.pdf)
                            merger.append(pdf_path)
                            os.remove(pdf_path)  # Deletes the individual PDF file after merging
                    merger.write(os.path.join(output_path, output_filename))

if __name__ == '__main__':
    main()
