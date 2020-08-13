import json
import os
import pprint

from jsonschema import Draft7Validator

from mosdex import records, read


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
                  format(problem_file, schema_file))
            pp = pprint.PrettyPrinter(indent=4)
            for error in sorted(validator.iter_errors(problem_json), key=str):
                print()
                pp.pprint(error.message)
        else:
            print("YES: Mosdex problem {} is a valid instance of Mosdex schema {}".
                  format(problem_file, schema_file))

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
        mosdex_classes = set([mosdex_entity[k_]["CLASS"] for k_ in mosdex_entity
                              if k_ not in mosdex_static_members])
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


def process_algorithm(mosdex: dict, do_print: bool = False):
    # Get the top-level members by class
    members = mosdex_members(mosdex['json'])

    # First, initialize the algorithm
    if "ALGORITHM" in members:
        mosdex_algorithm = members["ALGORITHM"]
    else:
        mosdex_algorithm = {"initialize_only": {"INITIALIZE": members["MODULE"].keys()}}

    # Execute the algorithm
    for name_, alg_ in mosdex_algorithm.items():
        print("**** Executing {} ****".format(name_))

        # Initialize
        process_initialize(mosdex, module_list=alg_["INITIALIZE"], do_print=do_print)


def process_recipe(mosdex: dict, mod_name, tab_name, do_print=True):
    mosdex_db = mosdex['db']
    table_name = mod_name + '_' + tab_name
    recipe_array = mosdex['json'][mod_name][tab_name]['RECIPE']

    sql_list = []
    for recipe in recipe_array:
        sql_list.append(recipe['DIRECTIVE'])
        sql_list.append(','.join(str(e) for e in recipe['PREDICATE']))

    sql_string = ' '.join(str(e) for e in sql_list)
    create_string = "CREATE TABLE " + table_name + ' AS ' + sql_string
    if do_print:
        print("\t\t\tRECIPE {}".format(create_string))

    mosdex_db.query(create_string)


def process_initialize(mosdex: dict, module_list=None, do_print=False):
    mosdex_db = mosdex["db"]

    if module_list is None:
        module_list = [k_ for k_ in mosdex['json'] if k_ in mosdex['json'].keys()
                       and mosdex['json'][k_]['CLASS'] is 'MODULE']

    for module_name in module_list:
        module = mosdex["json"][module_name]
        if do_print:
            print("\n\tModule {}".format(module_name))

        if "INITIALIZE" in module:
            init_sequence = module["INITIALIZE"]
        else:
            init_sequence = [k_ for k_ in module.keys() if k_ not in mosdex_static_members]

        if do_print:
            print("\tInitialization sequence: {}".format(init_sequence))

        for item in init_sequence:
            if module[item]['TYPE'] == 'OUTPUT':
                continue
            m1 = module[item]
            c1 = m1["CLASS"]
            t1 = m1['TYPE']
            table_name = module_name + '_' + item
            metadata = m1["METADATA"]
            if type(metadata["item_name"]) is list:
                for i in range(len(metadata["item_name"])):
                    n = metadata["item_name"][i]
                    t = metadata["item_type"][i]
                    u = metadata["item_usage"][i]
                    k = metadata["item_key"][i]
                    s = metadata["item_source"][i]
                    mosdex_db.query('INSERT INTO metadata_table (module_name, item_name, class_name,'
                                    'name, type, usage, key_type, source)'
                                    'VALUES(:mname, :iname, :cname, :nname, :tname, :uname,:kname, :sname)',
                                    mname=module_name, iname=item, cname=c1,
                                    nname=n, tname=t,
                                    uname=u, kname=k, sname=s)
            else:
                mosdex_db.query('INSERT INTO metadata_table (module_name, item_name, class_name,'
                                'name, type, usage, key_type, source)'
                                'VALUES(:mname, :iname, :cname, :nname, :tname, :uname, :kname, :sname)',
                                mname=module_name, iname=item, cname=c1,
                                nname=metadata["item_name"], tname=metadata["item_type"],
                                uname=metadata["item_usage"], kname=metadata["item_key"], sname=metadata["item_source"])
            if do_print:
                print("\t\t{}.{}.{}:".format(c1, module_name, item))
            if "RECIPE" in m1:
                process_recipe(mosdex, module_name, item, do_print=do_print)
                mosdex_db.query('INSERT INTO modules_table (module_name, item_name, class_name,'
                                'type_name, table_name)'
                                'VALUES(:mname, :iname, :cname, :tyname, :tname)',
                                mname=module_name, iname=item, cname=c1, tyname=t1, tname=table_name)
            if "UPDATE_RECIPE" in m1:
                continue
                # u1 = mosdex_recipe(m1["UPDATE_RECIPE"])
            if "INITIALIZE_FROM" in m1:
                table_name = m1["INITIALIZE_FROM"].replace('.', '_')
                mosdex_db.query('INSERT INTO modules_table (module_name, item_name, class_name,'
                                'type_name, table_name)'
                                'VALUES(:mname, :iname, :cname, :tyname, :tname)',
                                mname=module_name, iname=item, cname=c1, tyname=t1, tname=table_name)
            if "IMPORT_FROM" in m1:
                table_name = m1["IMPORT_FROM"].replace('.', '_')
                mosdex_db.query('INSERT INTO modules_table (module_name, item_name, class_name,'
                                'type_name, table_name)'
                                'VALUES(:mname, :iname, :cname, :tyname, :tname)',
                                mname=module_name, iname=item, cname=c1, tyname=t1, tname=table_name)
            if "SINGLETON" in m1:
                mosdex_db.query('INSERT INTO modules_table (module_name, item_name, class_name, '
                                'table_name) '
                                'VALUES(:mid, :mname, :iname, :cname, :tname)',
                                mname=module_name, iname=item, cname=c1,
                                tname="singletons_table")
                for s_name, s_value in m1["SINGLETON"].items():
                    r_value = None
                    if type(s_value) is str:
                        r_value = s_value
                        s_value = None
                    mosdex_db.query('INSERT INTO singletons_table (singleton_name, '
                                    's_value, s_recipe, module_name, item_name, class_name ) '
                                    'VALUES(:n, :v, :r, :m , :i, :c) ',
                                    n=s_name, v=s_value, r=r_value, m=module_name,
                                    i=item, c=c1)
            if "SCHEMA" in m1:
                mosdex_db.query('INSERT INTO modules_table (module_name, item_name, class_name,'
                                'type_name, table_name)'
                                'VALUES(:mname, :iname, :cname, :tyname, :tname)',
                                mname=module_name, iname=item, cname=c1, tyname=t1, tname=table_name)
                sql_list = []
                arg_list = []
                val_list = []
                for col_name, col_type in m1["SCHEMA"].items():
                    sql_list.append(col_name + ' ' + col_type)
                    arg_list.append(col_name)
                    col_colon = ":" + col_name
                    val_list.append(col_colon)
                sql_string = ','.join([str(e) for e in sql_list])
                arg_string = ",".join([str(e) for e in arg_list])
                val_string = ",".join([str(e) for e in val_list])
                create_string = 'CREATE TABLE ' + table_name + '  (' + sql_string + ')'
                mosdex_db.query(create_string)
                insert_string = 'INSERT INTO ' + table_name + '(' + arg_string + ') VALUES(' + val_string + ')'
                for row in m1["INSTANCE"]:
                    row_dict = dict(zip(arg_list, row))
                    mosdex_db.query(insert_string, **row_dict)


def initialize_database(db_file: str, do_print=False):
    # Initialize database
    db = records.Database(db_file)

    # Create modules table
    db.query('DROP TABLE IF EXISTS modules_table')
    db.query('CREATE TABLE modules_table ( module_name text, item_name text, '
             'class_name text, type_name text, table_name text PRIMARY KEY) ')

    # Create the singletons table
    db.query('DROP TABLE IF EXISTS singletons_table')
    db.query('CREATE TABLE singletons_table ('
             'module_name text, item_name text, class_name text, singleton_name text, '
             's_value numeric, s_recipe text)')

    # Create the metadata table
    db.query('DROP TABLE IF EXISTS metadata_table')
    db.query('CREATE TABLE metadata_table ('
             'module_name text, item_name text, class_name text, '
             'name text, type text, usage text, key_type text, source text )')

    return db


def initialize_mosdex(mosdex, do_print=False):
    # Initialize database and counters
    mosdex['db'] = initialize_database(mosdex['db_file'],
                                       do_print=do_print)

    # Open and test the mosdex problem against the schema
    mosdex['json'], mosdex['is_valid'] = mosdex_open_and_test(mosdex['problem_file'],
                                                              mosdex['schema_file'],
                                                              do_print=do_print)


if __name__ == "__main__":
    # Provide the file and schema locations
    schema_dir = "data"
    file_dir = "data"
    mosdex_problem_file = "sailco_1-3.json"
    mosdex_schema_file = "MOSDEXSchemaV1-3-ajk.json"
    records_db = 'sqlite://sailco.db'

    cs_json, is_valid = mosdex_open_and_test(os.path.join(file_dir, mosdex_problem_file),
                                             os.path.join(schema_dir, mosdex_schema_file),
                                             do_print=True)

    cs_modules = mosdex_members(cs_json, do_print=True)["MODULE"]
    for k, m in cs_modules.items():
        print("\n{}".format(k))
        mosdex_depends(m, do_print=True)
        mosdex_members(m, do_print=True)
    print()

    # Initialize mosdex problem
    mosdexProblem = {'db_file': records_db,
                     'problem_file': os.path.join(file_dir, mosdex_problem_file),
                     'schema_file': os.path.join(file_dir, mosdex_schema_file)}

    initialize_mosdex(mosdexProblem, do_print=False)

    # Commence Algorithm processing
    process_algorithm(mosdexProblem, do_print=False)

    # List the tables
    print("\n***List the Tables***")
    db = mosdexProblem['db']
    for table in db.get_table_names():
        print("\n**{}**".format(table))
        print(db.query('SELECT * FROM ' + table).dataset)
