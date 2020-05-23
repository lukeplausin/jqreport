# JQReport
Quick and dirty report builder - build a summary report from any JSON data in seconds!

# Motivation

Data is beautiful, however JSON is not. This is why I created `JQReport`, it's supposed to be a way to make key-value style data more understandable to humans.

Using this tool you can build a HTML report in seconds from almost any data. The report tries to make key features of the data more understandable to humans. It will try to build searchable tables out of flat dictionaries or dictionary lists, tell you key statistics about your data, and present it in a human friendly format.

# Installation

`pip install git+https://github.com/lukeplausin/jqreport.git`

# Usage

You can build a report from an input file.

`jqreport -f my_data_file.json -o my_report.html`

You can pipe data directly into it.

`cat my_data_file.json | jqreport -o my_report.html`

Use any data source!

`aws s3api list-buckets | jqreport`

And it works great with JQ [https://stedolan.github.io/jq/manual/](https://stedolan.github.io/jq/manual/)

`aws s3api list-buckets | jq '.Contents | [ .[] | select(.LastModified < "2020") ]' | jqreport`

Also works great with YAML (even with custom tags!)
Use the `--open-output` switch to open the output file in your browser.

`curl https://raw.githubusercontent.com/aws-quickstart/quickstart-microsoft-activedirectory/master/templates/ad-1.template | jqreport --open-output`

In case you like short command line tools, there is a short version

`cat data.json | jqr`
