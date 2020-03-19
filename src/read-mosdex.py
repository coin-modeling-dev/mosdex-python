import json
import os
from jsonschema import Draft7Validator
import pprint

schema_dir = "data"
file_dir = "data"

file = "cuttingStock_1-2.json"
with open(os.path.join(file_dir, file)) as f:
    cs_json = json.load(f)

schema_file = "MOSDEXSchemaV1-2-ajk.json"
with open(os.path.join(schema_dir, schema_file)) as f:
    mosdex_schema = json.load(f)

pp = pprint.PrettyPrinter(indent=8)


def is_it_valid():
    v1 = Draft7Validator(mosdex_schema)
    print("Is the file {} a valid instance of {}: {}".format(file, schema_file, v1.is_valid(cs_json)))
    print()

    for error in sorted(v1.iter_errors(cs_json), key=str):
        print()
        pp.pprint(error.message)
        print()


static_members = ["SYNTAX", "CLASS", "HEADING"]


def mosdex_members(mosdex_problem: dict, do_print=False):
    mosdex_classes = set([mosdex_problem[k]["CLASS"] for k in mosdex_problem
                          if k not in static_members])
    members = {}
    for m in mosdex_classes:
        members[m] = [k for k in mosdex_problem
                      if k not in static_members and mosdex_problem[k]["CLASS"] == m]
        if do_print:
            print("{:12s} {}".format(m, members[m]))
    return members


# print out the high level members of the mosdex problem
problems = mosdex_members(cs_json, do_print=True)
for p in problems["PROBLEM"]:
    print("\n{}".format(p))
    mosdex_members(cs_json[p], do_print=True)
