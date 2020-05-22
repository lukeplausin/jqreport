# This module is all about automating different views of data.
import json
import pkg_resources
from jinja2 import Template
import os

template_file = pkg_resources.resource_filename(
    __name__, os.path.join('templates', "page.html.j2"))
with open(template_file, 'r') as f:
    top_level_template = Template(f.read())
    

class Cognition:
    def __init__(self, data, key='_'):
        self.data = data
        self.key = key

        # Let's try to make some guesses about the data....
        

    def __str__(self):
        # Really basic hello world style thing to start with
        return json.dumps(self.data, indent=2)
    
    def top_level(self):
        # Create the document using this object as the top level.
        # with open()
        return top_level_template.render(
            data=self.data, formatted=json.dumps(self.data, indent=2), key=self.key)
        