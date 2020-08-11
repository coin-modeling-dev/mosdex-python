from mosdex.read import *


def initialize_tables(mosdex_problem: dict):
    db_ = mosdex_problem['db']

    # Create independent variables table
    db_.query('DROP TABLE IF EXISTS independent_variables')
    db_.query('CREATE TABLE independent_variables ( module text, variable text KEY, '
              'type text,'
              'lower_bound numeric, upper_bound numeric, value numeric, dual numeric) ')

    # Create dependent variables table
    db_.query('DROP TABLE IF EXISTS dependent_variables')
    db_.query('CREATE TABLE dependent_variables ( module text, variable text KEY, '
              'type text,'
              'lower_bound numeric, upper_bound numeric, value numeric, dual numeric) ')


def populate_independents(mosdex_problem: dict, do_print=False):
    db_ = mosdex_problem['db']

    # Get list of independent variables
    sql = 'SELECT module_name, item_name, class_name, type_name, table_name ' \
          'FROM modules_table WHERE class_name == "VARIABLE"'

    independent_variables = db_.query(sql)

    if do_print:
        print("\n{}:".format("Independent Variables"))
        for r in independent_variables:
            print("\t{}\t{}\t{}\t{}\t{}".format(r.module_name, r.item_name, r.class_name,
                                                r.table_name, r.type_name))

    lin_obj = []
    for r in independent_variables:
        module = r.module_name
        variable = r.item_name
        table_ = r.table_name
        variable_type = r.type_name
        sql = 'SELECT Column, LowerBound, UpperBound, Objective FROM ' + table_
        variable_definitions = db_.query(sql)

        if do_print:
            name = module + "_" + variable
            print("Variable: {}".format(name))
            for r1 in variable_definitions:
                print("\t{} {} {} {}".format(r1.Column, r1.LowerBound, r1.UpperBound, r1.Objective))

        for r1 in variable_definitions:
            db_.query('INSERT INTO independent_variables (module, variable, '
                      'type, lower_bound, upper_bound) '
                      'VALUES(:m, :v, :t, :l , :u) ',
                      m=module, v=r1.Column, t=variable_type, l=r1.LowerBound,
                      u=r1.UpperBound)

            if r1.Objective is not None:
                lin_obj.append({"Module": module, "Row": "OBJECTIVE",
                                "Column": r1.Column, "Coefficient": r1.Objective})

    mosdex_problem["linear_objective"] = lin_obj


def populate_dependents(mosdex_problem: dict, do_print=False):
    db_ = mosdex_problem['db']

    # Get list of dependent variables
    sql = 'SELECT module_name, item_name, class_name, type_name, table_name ' \
          'FROM modules_table WHERE class_name == "CONSTRAINT"'

    dependent_variables = db_.query(sql)

    if do_print:
        print("\n{}:".format("Dependent Variables"))
        for r in dependent_variables:
            print("\t{}\t{}\t{}\t{}\t{}".format(r.module_name, r.item_name, r.class_name,
                                                r.table_name, r.type_name))

    for r in dependent_variables:
        module = r.module_name
        table_ = r.table_name
        variable_type = r.type_name
        sql = 'SELECT * FROM ' + table_
        variable_definitions = db_.query(sql)

        for r1 in variable_definitions:
            if "RHS" in r1.keys():
                lower_bound = r1.RHS
                upper_bound = r1.RHS
                if r1.Sense == "LE":
                    lower_bound = "infinity"
                elif r1.Sense == "GE":
                    upper_bound = "infinity"
            else:
                lower_bound = r1.LowerBound
                upper_bound = r1.UpperBound

            db_.query('INSERT INTO dependent_variables (module, variable, '
                      'type, lower_bound, upper_bound) '
                      'VALUES(:m, :v, :t, :l , :u) ',
                      m=module, v=r1.Row, t=variable_type, l=lower_bound,
                      u=upper_bound)

    if mosdex_problem["linear_objective"] is not None:
        lin_obj = mosdex_problem["linear_objective"]
        modules = []
        for coeff in lin_obj:
            modules.append(coeff["Module"])
        for m_ in set(modules):
            db_.query('INSERT INTO dependent_variables (module, variable, '
                      'type, lower_bound, upper_bound) '
                      'VALUES(:m, :v, :t, :l , :u) ',
                      m=m_, v="Objective", t="LINEAR", l="infinity", u="infinity")


if __name__ == "__main__":
    # Provide the file and schema locations
    schema_dir = "data"
    file_dir = "data"
    mosdex_problem_file = "sailco_1-3.json"
    mosdex_schema_file = "MOSDEXSchemaV1-3-ajk.json"
    records_db = 'sqlite://'

    # Initialize mosdex problem
    mosdexProblem = {'db_file': records_db,
                     'problem_file': os.path.join(file_dir, mosdex_problem_file),
                     'schema_file': os.path.join(file_dir, mosdex_schema_file)}

    initialize_mosdex(mosdexProblem, do_print=False)
    process_algorithm(mosdexProblem, do_print=False)

    # Commence generation of base structure
    initialize_tables(mosdexProblem)
    populate_independents(mosdexProblem, do_print=True)
    populate_dependents(mosdexProblem, do_print=True)

    # List the tables
    print("\n***List the Tables***")
    db = mosdexProblem['db']
    print("\n**{}**".format("Independent Variables"))
    print(db.query('SELECT * FROM independent_variables').dataset)
    print("\n**{}**".format("Dependent Variables"))
    print(db.query('SELECT * FROM dependent_variables').dataset)
    # for table in db.get_table_names():
    #     print("\n**{}**".format(table))
    #     print(db.query('SELECT * FROM ' + table).dataset)
