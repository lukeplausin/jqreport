# JQReport
Quick and dirty report builder - build a summary report from any JSON data in seconds!

## Installation

`pip install git+https://github.com/lukeplausin/jqreport.git`

## Usage

You can build a report from an input file.

`jqreport -f my_data_file.json -o my_report.html`

You can pipe data directly into it.

`cat my_data_file.json | jqreport -o my_report.html`

Use any data source!

`aws s3api list-buckets | jqreport`

