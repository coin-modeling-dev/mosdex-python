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
    mosdex_problem_file = "cuttingStock_1-3.json"
    mosdex_schema_file = "MOSDEXSchemaV1-3-ajk.json"

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
        print("\n\n***{}***".format(k))
        for k1, m1 in m.items():
            mosdex_data_io = m1["TYPE"]
            if "RECIPE" in m1:
                print("\t{}.{}.{}:".format(k, k1, mosdex_data_io))
                for step in m1["RECIPE"]:
                    print("\t\t{}".format(step))
            if "SINGLETON" in m1:
                print("\t{}.{}.{}:".format(k, k1, mosdex_data_io))
                print("\t\t{}: {}".format("SINGLETON", m1["SINGLETON"]))
            if "SCHEMA" in m1:
                print("\t{}.{}.{}:".format(k, k1, mosdex_data_io))
                print("\t\t{}: {}".format("SCHEMA", m1["SCHEMA"]))
                if "INSTANCE" in m1:
                    print("\t\t{}: {}".format("INSTANCE", m1["INSTANCE"]))

    db = records.Database('sqlite://')

    # Create modules table
    db.query('DROP TABLE IF EXISTS modules_table')
    db.query('CREATE TABLE modules_table ( module_id integer KEY, module_name text, item_name text, '
             'table_name text, recipe_name text, '
             'CONSTRAINT module_item_pair PRIMARY KEY (module_name, item_name)) ')

    # Create the singletons table
    db.query('DROP TABLE IF EXISTS singletons_table')
    db.query('CREATE TABLE singletons_table ( singleton_id integer KEY, '
             'module_name text, item_name text, singleton_name text, '
             's_value number, s_recipe text)')

    print("\n\n***Process the modules***")
    # Process the modules
    modules_id = 0
    singletons_id = 0
    for k, m in cs_modules.items():

        # add the data items
        data = mosdex_members(m)["DATA"]
        for k1, m1 in data.items():
            if "SINGLETON" in m1:
                recipe_name = None
                db.query('INSERT INTO modules_table (module_id, module_name, item_name, table_name, recipe_name) '
                         'VALUES(:mid, :mname, :iname, :tname, :rname)',
                         mid=modules_id, mname=k, iname=k1, tname="singletons_table", rname=recipe_name)
                modules_id += 1
                print("\t{}.{}:".format(k, k1))
                for s_name, s_value in m1["SINGLETON"].items():
                    r_value = None
                    if type(s_value) is str:
                        r_value = s_value
                        s_value = None
                    db.query('INSERT INTO singletons_table (singleton_id, singleton_name, '
                             's_value, s_recipe, module_name, item_name ) '
                             'VALUES(:s_id, :n, :v, :r, :m , :i) ',
                             s_id=singletons_id, n=s_name, v=s_value, r=r_value, m=k, i=k1)
                    singletons_id += 1
            if "SCHEMA" in m1:
                table_name = k1 + '_table'
                db.query('INSERT INTO modules_table (module_id, module_name, item_name, table_name, recipe_name)'
                         'VALUES(:module_id, :mname, :iname, :tname, :rname)',
                         module_id=modules_id, mname=k, iname=k1, tname=table_name, rname=None)
                modules_id += 1
                sql_string = 'CREATE TABLE ' + table_name + '  (' + k1 + '_id integer PRIMARY KEY'
                table_id = k1 + '_id'
                arg_string = ' (' + table_id
                val_string = ' (' + ':' + table_id
                col_list = [table_id]
                for col_name, col_type in m1["SCHEMA"].items():
                    sql_string = sql_string + ', ' + col_name + ' ' + col_type
                    arg_string = arg_string + ', ' + col_name
                    val_string = val_string + ', ' + ':' + col_name
                    col_list.append(col_name)
                sql_string = sql_string + ')'
                arg_string = arg_string + ')'
                val_string = val_string + ')'
                print("\t{}".format(sql_string))
                print("\t{}".format(arg_string))
                print("\t{}".format(val_string))
                db.query(sql_string)
                count = 0
                for row in m1["INSTANCE"]:
                    row.insert(0, count)
                    row_dict = dict(zip(col_list, row))
                    print("\t{}".format(row_dict))
                    db.query('INSERT INTO ' + table_name + arg_string + ' VALUES ' + val_string, **row_dict)

                    count += 1

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

