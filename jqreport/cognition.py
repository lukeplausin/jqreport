# This module is all about automating different views of data.
import json
import pkg_resources
from jinja2 import Template
import os
import logging
import statistics

from jinja2 import Environment, PackageLoader, select_autoescape

DICTLIST_DICT_MIN_RATIO = 0.5

logger = logging.getLogger(__name__)

env = Environment(
    loader=PackageLoader('jqreport', 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
)

template_top_level = env.get_template('page.html.j2')
template_scalar = env.get_template('scalar.html.j2')

def simplicity(obj):
    # Rate the simplicity of the dictionary. Lower number is more simple.
    # 0 == scalar, 1 == list / flat, 2 == table, 3+ == complex
    if not obj:
        logger.debug("Object is null or empty, score 0")
        return 0
    if isinstance(obj, dict):
        if len(obj) == 1:
            logger.debug("Object is scalar dict, delegating to only child")
            return simplicity(list(obj.values())[0])
        logger.debug("Iterating over dict entries")
        max_rval = 0
        for k, v in obj.items():
            logger.debug("key: {}, value: {}".format(k, v))
            child_simplicity = simplicity(v)
            max_rval = max(max_rval, child_simplicity)
            if max_rval >= 2:
                # no point going further, child is a horrible mess of tangled 
                # json and jumbled lists, break now while we're ahead
                logger.debug("Key {} has score {}, object score {}".format(
                    k, child_simplicity, child_simplicity + 1))
                return max_rval + 1
        logger.debug("Dictionary non-trivial, but contents are simple, score 1.")
        return max_rval + 1

    elif isinstance(obj, list):
        if len(obj) == 0:
            logger.debug("List is empty, score 0")
            return 0 # Empty or scalar, simple
        elif len(obj) == 1:
            logger.debug("Object is scalar list, delegating to only child")
            return simplicity(obj[0])
        else:
            max_rval = 0
            logger.debug("Iterating over list entries")
            for idx, v in enumerate(obj):
                child_simplicity = simplicity(v)
                max_rval = max(max_rval, child_simplicity)
                if max_rval >= 2:
                    # no point going further, child is a horrible mess of tangled 
                    # json and jumbled lists, break now while we're ahead
                    logger.debug("Index {} has score {}, object score {}".format(
                        idx, child_simplicity, child_simplicity + 1))
                    return max_rval + 1

            logger.debug("List non-trivial, but contents are simple, score 1.")
            return max_rval + 1

    else:
        # This object is scalar
        logger.debug("Object is scalar, score 0.")
        return 0

# simplicity(data)
def interpret_data(data, key='.'):
    if not data:
        # Data is null, empty or "None".
        return str(data)
    if isinstance(data, list):
        # Try to gather useful information from the list
        if len(data) == 1:
            # Perhaps I should create a new class for this..
            print("Object is simple, return recursion.")
            return interpret_data(data[0], key="{}[0]".format(key))

        # I am a list... let's look at elements
        else:
            modal_type = statistics.mode([el.__class__ for el in data])
            if modal_type and modal_type == dict and simplicity(data) <= 2:
                # return CognitionDictList(data=data, key=key)
                try:
                    return CognitionDictList(data=data, key=key)
                except Exception as e:
                    # Doesn't work for some reason...
                    return CognitionList(data=data, key=key)

            else:
                # List contains complex or generic types, return other
                return CognitionList(data=data, key=key)
    elif isinstance(data, dict):
        # data is dictionary, check if simple or complex
        if len(data) == 1:
            sub_key = list(data.keys())[0]
            return interpret_data(data[sub_key], key="{}.{}".format(key.rstrip('.'), sub_key))
        elif simplicity(data) <= 2:
            return CognitionDictFlat(data=data, key=key)
        else:
            return CognitionDict(data=data, key=key)
    else:
        print("Data is a scalar, return a simple template")
        return Cognition(data=data, key=key, template=template_scalar)

class Cognition:
    def __init__(self, data, key='.', template=template_top_level):
        self.data = data
        self.key = key
        self.template = template
        self.interpret()

    def __str__(self):
        # Really basic hello world style thing to start with
        # if self.template:
        # return json.dumps(self.data, indent=2)
        return self.render()

    def interpret(self):
        # Let's try to make some guesses about the data.
        # Try to work out how to display myself....
        if isinstance(self.data, list) or isinstance(self.data, dict):
            # Complex type, interpret data
            self.contents = interpret_data(data=self.data, key=self.key)
        else:
            self.contents = str(self.data)

    def render(self):
        # Create the document.
        return self.template.render(
            contents=self.contents, raw=json.dumps(self.data, indent=2), key=self.key)

template_list = env.get_template('scalar.html.j2')
class CognitionList(Cognition):
    # TODO
    def __init__(self, data, key, template=template_list):
        super(CognitionList, self).__init__(data, key, template)
    # contents will probably need to be overloaded for this one...
    # This is where the smart stuff about analysing strings numbers etc for similarity goes...

                # else:
                #     return CognitionList(data=data, key=key)
                # elif modal_type == str:
                #     # list of strings - do something special in there..
                #     return CognitionList(data=data, key=key)
                # elif modal_type == int or modal_type == float:
                #     # list of numbers
                #     return CognitionList(data=data, key=key)
                # else:
                #     # list of unknown type
                #     return CognitionList(data=data, key=key)
            # else:
            #     # List of null, TODO
            #     return None
    def interpret(self):
        # This is just temporary
        self.contents = str(self.data)

template_dictlist = env.get_template('dictlist.html.j2')
class CognitionDictList(Cognition):
    # TODO - display missing keys, allow sort on table, paginate for long lists,
    # show some charts for basic stuff if the data is suitable
    # .e.g. date histogram for date fields, pie chart for low cardinality fields
    def __init__(self, data, key, template=template_dictlist):
        super(CognitionDictList, self).__init__(data, key, template)
        print("Dictlist created")
    # contents will probably need to be overloaded for this one...

    def interpret(self):
        # Let's try to make some guesses about the data.
        # Try to work out how to display myself....
        if not isinstance(self.data, list):
            raise Exception("DictList data must be a list")
        else:
            # First pass analysis - how many objects are dicts,
            # how many keys are shared?
            self.dict_count = 0
            self.key_counts = dict()
            for d in self.data:
                if isinstance(d, dict):
                    self.dict_count = self.dict_count + 1
                    for k, v in d.items():
                        self.key_counts[k] = self.key_counts.get(k, 0) + 1
                        # TODO - analyse types in v?

            # Ideal: 1, can still work well with around 0.5
            self.dict_ratio = self.dict_count / len(self.data)
            self.table_keys = []
            if self.dict_ratio >= DICTLIST_DICT_MIN_RATIO:
                for k, count in self.key_counts.items():
                    if count / len(self.data) >= DICTLIST_DICT_MIN_RATIO:
                        # Only include dict keys if they appear in enough entries
                        self.table_keys.append(k)
                self.contents = {
                    "data": self.data,
                    "dict_ratio": self.dict_ratio,
                    "table_keys": self.table_keys,
                    "key_counts": self.key_counts,
                    "ratio": DICTLIST_DICT_MIN_RATIO
                }

            else:
                # Too few objects to display as a table, let's 
                # show a list instead
                raise Exception("Too few dictionaries in list to display as table.")


class CognitionDict(Cognition):
    # TODO
    # Generic dictionary object, holds embedded kvs
    def __init__(self, data, key, template=template_scalar):
        super(CognitionDict, self).__init__(data, key, template)
    # contents will probably need to be overloaded for this one...

    def interpret(self):
        # Let's try to make some guesses about the data.
        if not isinstance(self.data, dict):
            raise Exception("CognitionDict data must be a dict")
        else:
            # This is a complex type, child entries should be interpreted also.
            self.contents = {
                "data": {
                    k: interpret_data(
                        data=v,
                        key="{}.{}".format(self.key, k)
                    )
                    for k, v in self.data.items()
                },
                "key_counts": len(self.data.keys()),
            }


template_simple_kv = env.get_template('simple_kv.html.j2')
class CognitionDictFlat(CognitionList):
    # TODO
    # Simple (flat) dictionary - this can probably be displayed as a table
    def __init__(self, data, key, template=template_simple_kv):
        super(CognitionDictFlat, self).__init__(data, key, template)
    # contents will probably need to be overloaded for this one...

    def interpret(self):
        # Let's try to make some guesses about the data.
        # Try to work out how to display myself....
        if not isinstance(self.data, dict):
            raise Exception("CognitionDictFlat data must be a dict")
        else:
            # This class is made for flat dictionaries... 
            # other types should work but might not display properly
            self.contents = {
                "data": self.data,
                "key_counts": len(self.data.keys()),
            }
