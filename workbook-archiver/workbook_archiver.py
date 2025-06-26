"""Module for exporting workbooks from a Tableau Server or Cloud site.

This script:
- Connects to a Tableau server using a personal access token.
- Queries all sites accessible to the user.
- Queries all workbooks in each site.
- Downloads the workbooks to a structured folder hierarchy by site and project.

Note:
- Nested projects are not handled; projects are uniquely identified by their ID.

"""

import argparse
import os
import tableauserverclient as TSC

# Characters not allowed in filenames (will be replaced with underscores)
ILLEGAL_CHARS = ["/","\\",":","|","*","?","<",">",'"']

### ~~ FUNCTIONS ~~ ###

def query_sites(server,tableau_auth):
    """
    Get a list of all accessible sites on the Tableau Server.

    Args:
        server (TSC.Server): Tableau Server instance.
        tableau_auth (TSC.PersonalAccessTokenAuth): Authentication object.

    Returns:
        list of dict: Each dict contains 'id', 'name', and 'site_uri' of a site.
    """
    site_list = []
    # sign into the server
    with server.auth.sign_in(tableau_auth):
        # list out all the sites
        for site in TSC.Pager(server.sites):
            # get key info for each site and append
            site_list.append({
                "id":site.id,
                "name":site.name,
                "site_uri":site.content_url
                })
        # output the full list of site info
        return site_list

def build_project_hierarchy(server, tableau_auth):
    """
    Builds a lookup of project_id -> full folder path by traversing parent_id hierarchy.

    Args:
        server (TSC.Server): Tableau server instance.
        tableau_auth (TSC.PersonalAccessTokenAuth): Auth object.

    Returns:
        dict: project_id -> full_path (e.g., "Department/Finance/Quarterly Reports")
    """
    project_lookup = {}

    with server.auth.sign_in(tableau_auth):
        all_projects = list(TSC.Pager(server.projects))
        id_to_project = {proj.id: proj for proj in all_projects}

        def get_full_path(project_id):
            path = []
            current = id_to_project.get(project_id)
            while current:
                name = current.name or "Unnamed"
                for c in ILLEGAL_CHARS:
                    name = name.replace(c, "_")
                path.insert(0, name)
                current = id_to_project.get(current.parent_id)
            return os.path.join(*path)

        for project_id in id_to_project:
            project_lookup[project_id] = get_full_path(project_id)

    return project_lookup

# function to get all workbooks for the site
def query_workbook_ids(server, tableau_auth):
    """
    Retrieve metadata for all workbooks in a given site.

    Args:
        server (TSC.Server): Tableau Server instance.
        tableau_auth (TSC.PersonalAccessTokenAuth): Authentication object.

    Returns:
        list of dict: Each dict contains workbook metadata.
    """
    workbook_list = []
    # sign into the site
    with server.auth.sign_in(tableau_auth):
        # list out all the workbooks
        for wb in TSC.Pager(server.workbooks):
            # for each workbook, get key info
            workbook_list.append({
                "id":wb.id,
                "name":wb.name,
                "project_id":wb.project_id,
                "project_name":wb.project_name,
                "content_url":wb.content_url,
                "owner_id":wb.owner_id
                })
    # output full list of workbook info
    return workbook_list

# function to download workbooks
def download_workbooks(server, tableau_auth,
                       workbook_info:str,
                       site_name:str,
                       output:str,
                       project_paths:str):
    """
    Download all workbooks in the provided list to the output directory.

    Args:
        server (TSC.Server): Tableau Server instance.
        tableau_auth (TSC.PersonalAccessTokenAuth): Authentication object.
        workbook_info (list of dict): List of workbook metadata.
        site_name (str): Name of the Tableau site.
        output (str): Root output directory.
    """
    # for each workbook in the full data set
    for wb in workbook_info:
        workbook_id = wb['id']
        project_id = wb['project_id']
        # clean up project name if it's in a personal space
        project_name = wb["project_name"] or "None"
        workbook_name = wb['name']

        # Santizie names
        for c in ILLEGAL_CHARS:
            project_name = project_name.replace(c,"_")
            workbook_name = workbook_name.replace(c,"_")
            site_name = site_name.replace(c, "_")

        # Create project-specific output directory
        project_path = project_paths.get(project_id, f"unknown_project_{project_id}")
        project_dir = os.path.join(output,site_name,project_path)
        os.makedirs(project_dir, exist_ok=True)

        # Construct full filepath (without extension as that is handled by TSC)
        filepath = os.path.normcase(os.path.join(project_dir, workbook_name))

        # Download the workbook
        with server.auth.sign_in(tableau_auth):
            server.workbooks.download(workbook_id,filepath=filepath)

### ~~~ MAIN ENTRY POINT ~~~ ###

# query all the sites
def main():
    """
    Entry point for CLI usage.
    Parses arguments, authenticates, queries workbooks from each site,
    and downloads them into an organized folder structure.
    """
    parser = argparse.ArgumentParser(
        description="Export all workbooks from Tableau Server or Tableau Cloud for archiving."
    )
    parser.add_argument("server", help="Tableau server URL e.g. https://tableau.example.com/")
    parser.add_argument("pat_name", help="Personal Access Token name")
    parser.add_argument("pat_secret", help="Personal Access Token secret")
    parser.add_argument("output",
                        help="Output directory path e.g. \"C:\\Users\\Name\\Downloads\\Archive\""
                        )
    parser.add_argument("--initial-site",
                        help="If provided, uri of the site to use during site querying")

    args = parser.parse_args()

    # check if the server address provided includes a trailing slash
    if not args.server.endswith("/"):
        args.server += "/"

    is_cloud = ".online.tableau.com" in args.server.lower()

    if is_cloud and not args.initial_site:
        parser.error("The --initial-site argument is required when using Tableau Cloud.")

    # Determine which site to use for initial login, uses Default site if not provided
    default_site_uri = args.initial_site if args.initial_site else ''

    # Create server instance and authenticate to get list of sites
    server = TSC.Server(args.server, use_server_version=True)
    initial_auth = TSC.PersonalAccessTokenAuth(
                            args.pat_name,
                            args.pat_secret,
                            site_id=default_site_uri)

    if is_cloud:
        # Only operate on the single specified site
        cloud_site_uri = args.initial_site

        # Sanitize site name from URI
        for c in ILLEGAL_CHARS:
            site_name = cloud_site_uri.replace(c,"_")

        # Ensure site folder exists
        os.makedirs(os.path.join(args.output, site_name), exist_ok=True)

        # Use existing auth to 
        workbooks = query_workbook_ids(server, initial_auth)
        project_paths = build_project_hierarchy(server,initial_auth)
        download_workbooks(server, initial_auth, workbooks, site_name, args.output, project_paths)
    else:
        # Get all accessible sites
        all_sites = query_sites(server,initial_auth)

        # for each site
        for site in all_sites:
            # get the site name
            site_name = site['name']

            # Sanitize site name
            for c in ILLEGAL_CHARS:
                site_name = site_name.replace(c,"_")

            # Ensure site folder exists
            os.makedirs(os.path.join(args.output, site_name), exist_ok=True)

            # Authenticate for this specific site
            site_auth  = TSC.PersonalAccessTokenAuth(
                        args.pat_name,
                        args.pat_secret,
                        site_id=site['site_uri']
                        )

            # Retrieve and download all workbooks for the site
            workbooks = query_workbook_ids(server,site_auth)
            project_paths = build_project_hierarchy(server,site_auth)
            download_workbooks(server,site_auth,workbooks,site_name, args.output,project_paths)

if __name__ == "__main__":
    main()
