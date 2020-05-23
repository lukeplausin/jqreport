# This module is all about automating different views of data.
import json
import pkg_resources
from jinja2 import Template
import os
import logging
import statistics
import random

from jinja2 import Environment, PackageLoader, select_autoescape

TABLE_MIN_COLUMNS = 1
DICTLIST_DICT_MIN_RATIO = 0.6 # Number of list entries that must be dict for structure to render as dictlist
DICTLIST_DICT_KEY_MIN_RATIO = 0.1 # Minimum # of dicts which require key for it to be rendered in table
DICTDICT_DICT_KEY_MIN_RATIO = 0.6 # Minimum # of dicts which require key for it to be rendered in table
COMPLEXITY_SAMPLE_SIZE = 50   # Sample size for assessing complexity
COMPLEX_LENGTH_THRESHOLD = 100 # Length threshold for an object to be considered complex

logger = logging.getLogger(__name__)

env = Environment(
    loader=PackageLoader('jqreport', 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
)

template_top_level = env.get_template('page.html.j2')
template_scalar = env.get_template('scalar.html.j2')
template_dictlist = env.get_template('dictlist.html.j2')
template_simple_kv = env.get_template('simple_kv.html.j2')
template_complex_kv = env.get_template('complex_kv.html.j2')
# template_list = env.get_template('scalar.html.j2')
template_list = env.get_template('dictlist.html.j2')


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
        if len(obj.values()) > COMPLEX_LENGTH_THRESHOLD:
            logger.debug("Object is large (n={}), sampling elements at random".format(len(obj.keys())))
            sample = random.sample(obj.keys(), COMPLEXITY_SAMPLE_SIZE)
        else:
            sample = list(obj.keys())
        for k in sample:
            v = obj[k]
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
            if len(obj) > COMPLEX_LENGTH_THRESHOLD:
                logger.debug("Object is large (n={}), sampling elements at random".format(len(obj)))
                sample = random.sample(obj, COMPLEXITY_SAMPLE_SIZE)
            else:
                logger.debug("Iterating over list entries")
                sample = obj
            max_rval = 0
            for idx, v in enumerate(sample):
                child_simplicity = simplicity(v)
                max_rval = max(max_rval, child_simplicity)
                if max_rval >= 3:
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

# 1: Render lists, # 2: stop embedded tables..
# TODO fix bug - pass thru key being hidden in single value dicts. eg cfn.yaml conditions
# TODO fix bug - stop dictionaries being rendered as dictlists or flatdicts if 
# # already inside a dictlist or flatdict eg cfn.yaml resources block (looks awful)
# TODO improve styling - try to make the structure stand out a bit more
# TODO fix bug - kv inside table renders badly and doesnt collapse
# TODO in some cases flat dict rendering is better even if it contains other dicts.
# Maybe check length vs depth of keys / values?
# TODO: List template
# TODO: Find a way to match up the parent and child html templates in a more graceful way
# TODO: Make source and keypath viewable from any element (how?)
# TODO: Render dictionary of dictionaries as a dictlist if children share keys, eg cfn parameters

# simplicity(data)
def interpret_data(data, key='.', allow_table=True):
    if not data:
        # Data is null, empty or "None".
        return str(data)
    if isinstance(data, list):
        # Try to gather useful information from the list
        if len(data) == 1:
            # Perhaps I should create a new class for this..
            logger.debug("Object is simple, return recursion.")
            return interpret_data(data[0], key="{}[0]".format(key))

        # I am a list... let's look at elements
        else:
            if not allow_table:
                logger.debug("Tables not allowed in context, exit early.")
                return CognitionList(data=data, key=key)

            if len(data) > COMPLEX_LENGTH_THRESHOLD:
                logger.debug("Object is long (n={}), sampling elements at random".format(len(data)))
                sample = random.sample(data, COMPLEXITY_SAMPLE_SIZE)
            else:
                sample = data
            try:
                modal_type = statistics.mode([el.__class__ for el in sample])
            except statistics.StatisticsError:
                # This can happen when types are mixed
                # I guess this is what's causing the issue...
                logger.info("Couldn't find modal type of object {}.".format(key))
                # Try to render as table
                modal_type = dict
            data_simplicity = simplicity(sample)
            logger.info("Object simplicity rating is {}".format(data_simplicity))
            if modal_type and modal_type == dict and data_simplicity <= 3:
                # return CognitionTable(data=data, key=key)
                try:
                    return CognitionTable(data=data, key=key)
                except Exception as e:
                    # Doesn't work for some reason...
                    logger.info("Couldn't format object {} as dictlist.".format(key))
                    return CognitionList(data=data, key=key)

            else:
                # List contains complex or generic types, return other
                return CognitionList(data=data, key=key)
    elif isinstance(data, dict):
        # data is dictionary, check if simple or complex
        if len(data) == 1:
            sub_key = list(data.keys())[0]
            return interpret_data(data[sub_key], key="{}.{}".format(key.rstrip('.'), sub_key))
        else:
            data_simplicity = simplicity(data)
            logger.info("Object simplicity rating is {}".format(data_simplicity))
            if data_simplicity <= 2:
                return CognitionDictFlat(data=data, key=key)
            # elif data_simplicity == 2:
            #     return CognitionDict(data=data, key=key, template=template_simple_kv)
            else:
                try:
                    # Try to render as a table
                    return CognitionTable(data=data, key=key)
                except Exception as e:
                    # Doesn't work for some reason...
                    logger.info("Couldn't format object {} as table.".format(key))
                    return CognitionDict(data=data, key=key, template=template_complex_kv)
    else:
        logger.debug("Data is a scalar, return a simple template")
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
        # This is just a first attempt.. may want to add exceptions for other types
        self.contents = {
            "data": [
                interpret_data(
                    data=v,
                    key="{}[{}]".format(self.key, idx)
                )
                for idx, v in enumerate(self.data)
            ],
            "table_keys": ["entry"],
            "key_counts": len(self.data),
        }


class CognitionTable(Cognition):
    # This class represents table-like data. This can be dictionary lists, and
    # dictionaries of dictionaries if the child dictionaries share some keys.

    # TODO - display missing keys, allow sort on table, filter by keys
    # show some charts for basic stuff if the data is suitable
    # .e.g. date histogram for date fields, pie chart for low cardinality fields
    def __init__(self, data, key, template=template_dictlist):
        super(CognitionTable, self).__init__(data, key, template)
        logger.debug("Table created")

    def interpret(self):
        # Let's try to make some guesses about the data.
        # Try to work out how to display myself....
        if not (isinstance(self.data, list) or isinstance(self.data, dict)):
            logger.debug("Attempt to create CognitionTable with key: {}, data: {}".format(self.key, self.data))
            raise Exception("CognitionTable data must be a list or dict")
        else:
            # First pass analysis - how many objects are dicts,
            # how many keys are shared?
            self.dict_count = 0
            self.key_counts = dict()
            if isinstance(self.data, dict):
                child_iter = self.data.values()
                min_ratio = DICTDICT_DICT_KEY_MIN_RATIO
            else:
                child_iter = self.data
                min_ratio = DICTLIST_DICT_KEY_MIN_RATIO
            for d in child_iter:
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
                    if count / len(self.data) >= min_ratio:
                        # Only include dict keys if they appear in enough entries
                        self.table_keys.append(k)
                if len(self.table_keys) < TABLE_MIN_COLUMNS:
                    raise Exception("CognitionTable data has too few shared columns.")
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
    # Generic dictionary object, holds embedded kvs
    def __init__(self, data, key, template=template_simple_kv):
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

class CognitionDictFlat(CognitionList):
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
