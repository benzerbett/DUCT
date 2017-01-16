import collections
from collections import OrderedDict
import requests
import jsonref
import json
from flattentool.schema import get_property_type_set
from jsonschema.exceptions import ValidationError
from jsonschema.validators import Draft4Validator as validator
from jsonschema import FormatChecker, RefResolver
import re

import zoom_demo.lib.tools as tools

uniqueItemsValidator = validator.VALIDATORS.pop("uniqueItems")

LANGUAGE_RE = re.compile("^(.*_(((([A-Za-z]{2,3}(-([A-Za-z]{3}(-[A-Za-z]{3}){0,2}))?)|[A-Za-z]{4}|[A-Za-z]{5,8})(-([A-Za-z]{4}))?(-([A-Za-z]{2}|[0-9]{3}))?(-([A-Za-z0-9]{5,8}|[0-9][A-Za-z0-9]{3}))*(-([0-9A-WY-Za-wy-z](-[A-Za-z0-9]{2,8})+))*(-(x(-[A-Za-z0-9]{1,8})+))?)|(x(-[A-Za-z0-9]{1,8})+)))$")


def uniqueIds(validator, uI, instance, schema):
    if (
        uI and
        validator.is_type(instance, "array")
    ):
        non_unique_ids = set()
        all_ids = set()
        for item in instance:
            try:
                item_id = item.get('id')
            except AttributeError:
                # if item is not a dict
                item_id = None
            if item_id and not isinstance(item_id, list) and not isinstance(item_id, dict):
                if item_id in all_ids:
                    non_unique_ids.add(item_id)
                all_ids.add(item_id)
            else:
                # if there is any item without an id key, or the item is not a dict
                # revert to original validator
                for error in uniqueItemsValidator(validator, uI, instance, schema):
                    yield error
                return

        if non_unique_ids:
            yield ValidationError("Non-unique ID Values (first 3 shown):  {}".format(", ".join(str(x) for x in list(non_unique_ids)[:3])))


def required_draft4(validator, required, instance, schema):
    if not validator.is_type(instance, "object"):
        return
    for property in required:
        if property not in instance:
            yield ValidationError(property)


validator.VALIDATORS.pop("patternProperties")
validator.VALIDATORS["uniqueItems"] = uniqueIds
validator.VALIDATORS["required"] = required_draft4


def fields_present_generator(json_data, prefix=''):
    if not isinstance(json_data, dict):
        return
    for key, value in json_data.items():
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    yield from fields_present_generator(item, prefix + '/' + key)
            yield prefix + '/' + key
        elif isinstance(value, dict):
            yield from fields_present_generator(value, prefix + '/' + key)
            yield prefix + '/' + key
        else:
            yield prefix + '/' + key


def get_fields_present(*args, **kwargs):
    counter = collections.Counter()
    counter.update(fields_present_generator(*args, **kwargs))
    return dict(counter)


def schema_dict_fields_generator(schema_dict):
    if 'properties' in schema_dict:
        for property_name, value in schema_dict['properties'].items():
            if 'oneOf' in value:
                property_schema_dicts = value['oneOf']
            else:
                property_schema_dicts = [value]
            for property_schema_dict in property_schema_dicts:
                property_type_set = get_property_type_set(property_schema_dict)
                if 'object' in property_type_set:
                    for field in schema_dict_fields_generator(property_schema_dict):
                        yield '/' + property_name + field
                elif 'array' in property_type_set:
                    fields = schema_dict_fields_generator(property_schema_dict['items'])
                    for field in fields:
                        yield '/' + property_name + field
                yield '/' + property_name


class CustomJsonrefLoader(jsonref.JsonLoader):
    def __init__(self, **kwargs):
        self.schema_url = kwargs.pop('schema_url', None)
        super().__init__(**kwargs)

    def get_remote_json(self, uri, **kwargs):
        # ignore url in ref apart from last part
        uri = self.schema_url + uri.split('/')[-1]
        if uri[:4] == 'http':
            return super().get_remote_json(uri, **kwargs)
        else:
            with open(uri) as schema_file:
                return json.load(schema_file, **kwargs)


def get_schema_fields(schema_url, schema_name):
    if schema_url[:4] == 'http':
        r = requests.get(schema_url + schema_name)
        json_text = r.text
    else:
        with open(schema_url + schema_name) as schema_file:
            json_text = schema_file.read()

    return set(schema_dict_fields_generator(jsonref.loads(json_text, loader=CustomJsonrefLoader(schema_url=schema_url), object_pairs_hook=OrderedDict)))


def get_counts_additional_fields(schema_url, schema_name, json_data, context, current_app):
    fields_present = get_fields_present(json_data)
    schema_fields = get_schema_fields(schema_url, schema_name)
    data_only_all = set(fields_present) - schema_fields
    data_only = set()
    for field in data_only_all:
        parent_field = "/".join(field.split('/')[:-1])
        # only take fields with parent in schema (and top level fields)
        # to make results less verbose
        if not parent_field or parent_field in schema_fields:
            if current_app == 'cove-ocds':
                if LANGUAGE_RE.search(field.split('/')[-1]):
                    continue
            data_only.add(field)

    return [('/'.join(key.split('/')[:-1]), key.split('/')[-1], fields_present[key]) for key in data_only]


class CustomRefResolver(RefResolver):
    def __init__(self, *args, **kw):
        self.schema_url = kw.pop('schema_url')
        super().__init__(*args, **kw)

    def resolve_remote(self, uri):
        uri = self.schema_url + uri.split('/')[-1]
        document = self.store.get(uri)
        if document:
            return document

        if self.schema_url.startswith("http"):
            return super().resolve_remote(uri)
        else:
            with open(uri) as schema_file:
                result = json.load(schema_file)
            if self.cache_remote:
                self.store[uri] = result
            return result


validation_error_lookup = {"date-time": "Date is not in datetime format",
                           "uri": "Invalid 'uri' found",
                           "string": "Value is not a string",
                           "integer": "Value is not a integer",
                           "number": "Value is not a number",
                           "object": "Value is not an object",
                           "array": "Value is not an array"}


def get_schema_validation_errors(json_data, schema_url, schema_name, current_app, cell_source_map, heading_source_map):
    if schema_url.startswith("http"):
        schema = requests.get(schema_url + schema_name).json()
    else:
        with open(schema_url + schema_name) as schema_file:
            schema = json.load(schema_file)

    validation_errors = collections.defaultdict(list)
    format_checker = FormatChecker()
    if current_app == 'cove-360':
        format_checker.checkers['date-time'] = (tools.datetime_or_date, ValueError)
    for n, e in enumerate(validator(schema, format_checker=format_checker, resolver=CustomRefResolver('', schema, schema_url=schema_url)).iter_errors(json_data)):
        message = e.message
        path = "/".join(str(item) for item in e.path)
        path_no_number = "/".join(str(item) for item in e.path if not isinstance(item, int))

        validator_type = e.validator
        if e.validator in ('format', 'type'):
            validator_type = e.validator_value
            if isinstance(e.validator_value, list):
                validator_type = e.validator_value[0]

            new_message = validation_error_lookup.get(validator_type)
            if new_message:
                message = new_message

        value = {"path": path}
        cell_reference = cell_source_map.get(path)

        if cell_reference:
            first_reference = cell_reference[0]
            if len(first_reference) == 4:
                value["sheet"], value["col_alpha"], value["row_number"], value["header"] = first_reference
            if len(first_reference) == 2:
                value["sheet"], value["row_number"] = first_reference

        if not isinstance(e.instance, (dict, list)):
            value["value"] = e.instance

        if e.validator == 'required':
            field_name = e.message
            if len(e.path) > 2:
                if isinstance(e.path[-2], int):
                    parent_name = e.path[-1]
                else:
                    parent_name = e.path[-2]

                field_name = str(parent_name) + ":" + e.message
            heading = heading_source_map.get(path_no_number + '/' + e.message)
            if heading:
                field_name = heading[0][1]
                value['header'] = heading[0][1]
            message = "'{}' is missing but required".format(field_name)
        if e.validator == 'enum':
            header = value.get('header')
            if not header:
                header = e.path[-1]
            message = "Invalid code found in '{}'".format(header)

        unique_validator_key = [validator_type, message, path_no_number]
        validation_errors[json.dumps(unique_validator_key)].append(value)
    return dict(validation_errors)
