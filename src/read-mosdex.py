import json
import os
from jsonschema import Draft7Validator
import pprint


def mosdex_open_and_test(problem_file, schema_file, do_print=False):
    with open(problem_file) as f:
        problem_json = json.load(f)
    with open(schema_file) as f:
        schema_json = json.load(f)
    validator = Draft7Validator(schema_json)
    valid = validator.is_valid(problem_json)
    if do_print:
        if not valid:
            print("NO: Mosdex problem {} is not a valid instance of Mosdex schema {}".
                  format(mosdex_problem_file, mosdex_schema_file))
            pp = pprint.PrettyPrinter(indent=4)
            for error in sorted(validator.iter_errors(cs_json), key=str):
                print()
                pp.pprint(error.message)
        else:
            print("YES: Mosdex problem {} is a valid instance of Mosdex schema {}".
                  format(mosdex_problem_file, mosdex_schema_file))

        print()
    return problem_json, valid


def mosdex_members(mosdex_problem: dict, do_print=False):
    static_members = ["SYNTAX", "CLASS", "HEADING", "NAME"]
    mosdex_classes = set([mosdex_problem[k]["CLASS"] for k in mosdex_problem
                          if k not in static_members])
    members = {}
    for m in mosdex_classes:
        members[m] = [mosdex_problem[k] for k in mosdex_problem
                      if k not in static_members and mosdex_problem[k]["CLASS"] == m]
        if do_print:
            print("{:12s} {}".format(m, [k["NAME"] for k in members[m]]))
    return members


if __name__ == "__main__":
    # Provide the file and schema locations
    schema_dir = "data"
    file_dir = "data"
    mosdex_problem_file = "cuttingStock_1-2.json"
    mosdex_schema_file = "MOSDEXSchemaV1-2-ajk.json"

    # Open and test the mosdex problem against the schema
    cs_json, is_valid = mosdex_open_and_test(os.path.join(file_dir, mosdex_problem_file),
                                             os.path.join(schema_dir, mosdex_schema_file))

    # print out the high level members of the mosdex problem
    modules = mosdex_members(cs_json, do_print=True)
    for p in modules["MODULE"]:
        print("\n{}".format(p["NAME"]))
        mosdex_members(p, do_print=True)
