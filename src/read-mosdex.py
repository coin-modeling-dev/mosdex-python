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


mosdex_static_members = ["SYNTAX", "CLASS", "HEADING", "NAME", "DEPENDS"]
mosdex_types = ["INPUT", "OUTPUT"]


def mosdex_depends(mosdex_entity: dict, do_print=False):
    if "DEPENDS" in mosdex_entity.keys():
        if do_print:
            print("{:12s} {}".format("DEPENDS", mosdex_entity["DEPENDS"]))
        return mosdex_entity["DEPENDS"]
    else:
        return None


def mosdex_members(mosdex_entity: dict, mosdex_class=None, do_print=False):
    if mosdex_class is None:
        mosdex_classes = set([mosdex_entity[k]["CLASS"] for k in mosdex_entity
                              if k not in mosdex_static_members])
    else:
        mosdex_classes = [mosdex_class]

    members = {}
    for m1 in mosdex_classes:
        members[m1] = {}
        for k1, v in mosdex_entity.items():
            if k1 not in mosdex_static_members and mosdex_entity[k1]["CLASS"] == m1:
                members[m1][k1] = v
        if do_print:
            print("{:12s} {}".format(m1, list(members[m1].keys())))
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
    cs_modules = mosdex_members(cs_json, do_print=True)["MODULE"]
    for k, m in cs_modules.items():
        print("\n{}".format(k))
        mosdex_depends(m, do_print=True)
        mosdex_members(m, do_print=True)
    print()

    # Let's get the data
    cs_data = {}
    for k, m in cs_modules.items():
        cs_data[k] = mosdex_members(m)["DATA"]

    # Print out the data elements
    for k, m in cs_data.items():
        for k1, m1 in m.items():
            mosdex_data_io = m1["TYPE"]
            if "RECIPE" in m1:
                print("{}.{}.{}:".format(k, k1, mosdex_data_io))
                if "DEPENDS" in m1:
                    print("\t{}\t{}".format("DEPENDS", m1["DEPENDS"]))
                print("\t{}".format("RECIPE"))
                for step in m1["RECIPE"]:
                    print("\t\t{}".format(step))
            if "SINGLETON" in m1:
                print("{}.{}.{}:".format(k, k1, mosdex_data_io))
                print("\t{} {}".format("SINGLETON", m1["SINGLETON"]))
            if "SCHEMA" in m1:
                print("{}.{}.{}:".format(k, k1, mosdex_data_io))
                print("\t{} {}".format("SCHEMA", m1["SCHEMA"]))
                if "INSTANCE" in m1:
                    print("\t{} {}".format("INSTANCE", m1["INSTANCE"]))



