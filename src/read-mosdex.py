import json
import os
from jsonschema import Draft7Validator
import pprint

import sqlite3
from sqlite3 import Error

import records


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn


def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)


def create_module(conn, module_name):
    """
    Create a new project into the projects table
    :param conn:
    :param project:
    :return: project id
    """
    sql = ''' INSERT INTO modules(module_name)
              VALUES(?) '''
    cur = conn.cursor()
    cur.execute(sql, module_name)
    return cur.lastrowid


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
            for error in sorted(validator.iter_errors(problem_json), key=str):
                print()
                pp.pprint(error.message)
        else:
            print("YES: Mosdex problem {} is a valid instance of Mosdex schema {}".
                  format(mosdex_problem_file, mosdex_schema_file))

        print()
    return problem_json, valid


mosdex_static_members = ["SYNTAX", "CLASS", "HEADING", "NAME", "DEPENDS", "ALGORITHM", "INITIALIZE"]
mosdex_types = ["INPUT", "OUTPUT"]


def mosdex_recipe(recipe: list, do_print=False):
    recipe_string = ""
    for i in recipe:
        d = i["DIRECTIVE"]
        p = i["PREDICATE"]
        recipe_add = " ".join(d + p)
        recipe_string = recipe_string + " " + recipe_add
        if do_print:
            print(d, p, recipe_add)
    if do_print:
        print(recipe_string)
    return recipe_string


def mosdex_depends(mosdex_entity: dict, do_print=False):
    if "DEPENDS" in mosdex_entity.keys():
        if do_print:
            print("{:12s} {}".format("DEPENDS", mosdex_entity["DEPENDS"]))
        return mosdex_entity["DEPENDS"]
    else:
        return None


def mosdex_members(mosdex_entity: dict, mosdex_class=None, do_print=False) -> dict:
    if mosdex_class is None:
        mosdex_classes = set([mosdex_entity[k]["CLASS"] for k in mosdex_entity
                              if k not in mosdex_static_members])
    else:
        mosdex_classes = [mosdex_class]

    members_ = {}
    for m1 in mosdex_classes:
        members_[m1] = {}
        for k1, v in mosdex_entity.items():
            if k1 not in mosdex_static_members and mosdex_entity[k1]["CLASS"] == m1:
                members_[m1][k1] = v
        if do_print:
            print("{:12s} {}".format(m1, list(members_[m1].keys())))
    return members_


def process_algorithm(mosdex_entity: dict, do_print: object = False):
    algs_ = mosdex_entity["ALGORITHM"]
    for name_, alg_ in algs_.items():
        print("\n\n**** Executing {} ****\n".format(name_))
        for step_, value_ in alg_.items():
            if step_ == "INITIALIZE":
                print("\tAlgorithm {}: Step: {}".format(name_, "INITIALIZE"))
                process_initialize(mosdex_entity, module_list=value_, do_print=do_print)
        else:
            pass


if __name__ == "__main__":
    # Provide the file and schema locations
    schema_dir = "data"
    file_dir = "data"
    mosdex_problem_file = "cuttingStock_1-2.json"
    mosdex_schema_file = "MOSDEXSchemaV1-3-ajk.json"

    # Open and test the mosdex problem against the schema
    cs_json, is_valid = mosdex_open_and_test(os.path.join(file_dir, mosdex_problem_file),
                                             os.path.join(schema_dir, mosdex_schema_file),
                                             do_print=False)

    # print out the high level members of the mosdex problem
    cs_modules = mosdex_members(cs_json, do_print=True)["MODULE"]
    for k, m in cs_modules.items():
        print("\n{}".format(k))
        mosdex_depends(m, do_print=True)
        mosdex_members(m, do_print=True)
    print()

    # Initialize database
    db = records.Database('sqlite://')

    # Create modules table
    modules_id: int = 0
    db.query('DROP TABLE IF EXISTS modules_table')
    db.query('CREATE TABLE modules_table ( module_id integer KEY, module_name text, item_name text, '
             'class_name text, table_name text, recipe_string text, recipe_update text, '
             'CONSTRAINT module_item_pair PRIMARY KEY (module_name, item_name)) ')

    # Create the singletons table
    singletons_id: int = 0
    db.query('DROP TABLE IF EXISTS singletons_table')
    db.query('CREATE TABLE singletons_table ( singleton_id integer KEY, '
             'module_name text, item_name text, class_name text, singleton_name text, '
             's_value number, s_recipe text)')

    # Commence Algorithm processing
    mosdex_instance = mosdex_members(cs_json)
    mosdex_instance["modules_id"] = modules_id
    mosdex_instance["singletons_id"] = singletons_id
    mosdex_instance["database"] = db
    if "ALGORITHM" in mosdex_instance:
        process_algorithm(mosdex_instance, do_print=True)
    else:
        process_initialize(mosdex_instance, do_print=True)

    print("\n***List the Tables***")
    for table in db.get_table_names():
        print("\n**{}**".format(table))
        print(db.query('SELECT * FROM ' + table).dataset)

'''
    # Use in-memory database
    database = ':memory:'

    # create a database connection
    conn = create_connection(database)
    assert conn is not None

    # create the modules table
    sql_create_modules_table = """ CREATE TABLE IF NOT EXISTS modules (
                                        module_name text NOT NULL PRIMARY KEY,
                                    ); """
    create_table(conn, sql_create_modules_table)

    # add the module names to the modules table
    for k in cs_modules.keys():
        create_module(k)



    sql_create_tasks_table = """CREATE TABLE IF NOT EXISTS tasks (
                                    id integer PRIMARY KEY,
                                    name text NOT NULL,
                                    priority integer,
                                    status_id integer NOT NULL,
                                    project_id integer NOT NULL,
                                    begin_date text NOT NULL,
                                    end_date text NOT NULL,
                                    FOREIGN KEY (project_id) REFERENCES projects (id)
                                );"""

'''
