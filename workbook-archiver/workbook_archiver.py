"""Module for exporting workbooks from a Tableau Server or Cloud site.

This script:
- Connects to a Tableau server using a personal access token.
- Queries all sites accessible to the user.
- Queries all workbooks in each site.
- Downloads the workbooks to a structured folder hierarchy by site and project.

"""

import argparse
import os
from dataclasses import dataclass
import tableauserverclient as TSC

### ~~ CONSTANTS ~~ ###
# Characters not allowed in filenames (will be replaced with underscores)
ILLEGAL_CHARS = ["/","\\",":","|","*","?","<",">",'"']

@dataclass
class WorkbookContext:
    """
    A container for workbook export configuration and context.

    Attributes:
        server (TSC.Server): An authenticated Tableau Server instance.
        tableau_auth (TSC.PersonalAccessTokenAuth): Authentication credentials for the site.
        site_name (str): The sanitized name of the Tableau site (used in folder structure).
        output (str): The root path where workbooks will be saved locally.
        project_paths (dict): A mapping of project_id to its full nested folder path.
        no_extracts (bool): Whether to include embedded extracts when downloading workbooks.
    """
    server: TSC.Server
    tableau_auth: TSC.PersonalAccessTokenAuth
    site_name: str
    output: str
    project_paths: dict
    no_extracts: bool

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
def download_workbooks(ctx: WorkbookContext,
                       workbook_info:list[dict],
                       ):

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
        project_path = ctx.project_paths.get(project_id, f"unknown_project_{project_id}")
        project_dir = os.path.join(ctx.output,ctx.site_name,project_path)
        os.makedirs(project_dir, exist_ok=True)

        # Construct full filepath (without extension as that is handled by TSC)
        filepath = os.path.normcase(os.path.join(project_dir, workbook_name))

        # Download the workbook
        with ctx.server.auth.sign_in(ctx.tableau_auth):
            ctx.server.workbooks.download(workbook_id,filepath=filepath,no_extract=ctx.no_extracts)

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
    parser.add_argument("--no-extracts",
                        action="store_true",
                        help="If set, workbooks will be downloaded without embedded extracts")

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

        # Use existing auth to download
        workbooks = query_workbook_ids(server, initial_auth)
        project_paths = build_project_hierarchy(server,initial_auth)
        ctx = WorkbookContext(
            server=server,
            tableau_auth=initial_auth,
            site_name=site_name,
            output=args.output,
            project_paths=project_paths,
            no_extracts=args.no_extracts
        )
        download_workbooks(ctx, workbooks)
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
            ctx = WorkbookContext(
                server=server,
                tableau_auth=site_auth,
                site_name=site_name,
                output=args.output,
                project_paths=project_paths,
                no_extracts=args.no_extracts
                )
            download_workbooks(ctx, workbooks)

if __name__ == "__main__":
    main()
