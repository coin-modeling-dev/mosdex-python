import json
import os
from jsonschema import Draft7Validator
import pprint

example_dir = "../MOSDEX-Examples/MOSDEX-1.2"

cutting_stock_file = "cuttingStock_1-2.json"
with open(os.path.join(example_dir, cutting_stock_file)) as f:
    cs_json = json.load(f)

schema_file = "MOSDEXSchemaV1-2.json"
with open(os.path.join(example_dir, schema_file)) as f:
    mosdex_schema = json.load(f)

pp = pprint.PrettyPrinter(indent=8)


v = Draft7Validator(mosdex_schema)
print("Is the file {} a valid instance of {}: {}".format(cutting_stock_file, schema_file, v.is_valid(cs_json)))
print()

for error in sorted(v.iter_errors(cs_json), key=str):
    print()
    pp.pprint(error.message)
    print()
