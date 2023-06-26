# Tableau Server/Cloud FullPDF Downloader Script

This Python scripts emulates the download 'fullpdf' functionality that is available in the original version of tabcmd.

While the newer version of tabcmd can download all views in a workbook as a PDF, it is currently unable to apply a filter to all views.

This script aims to offer a replacement for that missing functionality until Tableau developers build the option into the REST API.

## How to run

Ensure you are using Python 3.7 or later. Run the script with

python /path/to/tableau_fullpdf_downloader.py -f /path/to/config.json, or
python /path/to/tableau_fullpdf_downloader.py -q

## Usage

The script requires a number of input variables, which can be provided interactively at runtime, or in a JSON file, as described below. To choose between these two options, specify one of the following arguments when running the script:

Use the argument '-f (filename)' to provide a JSON file as input
If using a file, see the config-example.json file for an example of the required format.

Use the argument '-q' to be prompted with questions.
If running interactively, you will be prompted at the command line to input all the variables.
