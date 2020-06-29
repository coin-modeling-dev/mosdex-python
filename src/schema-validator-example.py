import json
from jsonschema import Draft7Validator
import pprint


def json_test_schema(json_file, schema_file, do_print=False):
    with open(json_file) as f:
        json_instance = json.load(f)
    with open(schema_file) as f:
        schema_json = json.load(f)
    validator = Draft7Validator(schema_json)
    valid = validator.is_valid(json_instance)
    if do_print:
        if not valid:
            print("NO: {} is not a valid instance of schema {}".
                  format(json_file, schema_file))
            pp = pprint.PrettyPrinter(indent=4)
            for error in sorted(validator.iter_errors(json_instance), key=str):
                print()
                pp.pprint(error.message)
        else:
            print("YES: {} is a valid instance of schema {}".
                  format(json_file, schema_file))
    return json_instance, valid
