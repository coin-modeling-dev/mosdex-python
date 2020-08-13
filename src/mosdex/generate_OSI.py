import pandas as pd
import os

from mosdex import initialize_mosdex, process_algorithm


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
        sql = 'SELECT Name, LowerBound, UpperBound, Objective FROM ' + table_
        variable_definitions = db_.query(sql)

        if do_print:
            name = module + "_" + variable
            print("Variable: {}".format(name))
            for r1 in variable_definitions:
                print("\t{} {} {} {}".format(r1.Name, r1.LowerBound, r1.UpperBound, r1.Objective))

        for r1 in variable_definitions:
            db_.query('INSERT INTO independent_variables (module, variable, '
                      'type, lower_bound, upper_bound) '
                      'VALUES(:m, :v, :t, :l , :u) ',
                      m=module, v=r1.Name, t=variable_type, l=r1.LowerBound,
                      u=r1.UpperBound)

            if r1.Objective is not None:
                lin_obj.append({"Module": module, "Name": "OBJECTIVE",
                                "Name": r1.Name, "Coefficient": r1.Objective})

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
                      m=module, v=r1.Name, t=variable_type, l=lower_bound,
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
                      m=m_, v="OBJECTIVE", t="LINEAR", l="infinity", u="infinity")


def populate_expressions(mosdex_problem: dict, do_print=False):
    db_ = mosdex_problem["db"]

    # Linear Expressions
    linear_expressions = db_.query('SELECT module, variable FROM dependent_variables WHERE type == "LINEAR"')

    if linear_expressions is not None:

        # Drop the linear_expressions table
        db_.query('DROP TABLE IF EXISTS linear_expressions')

        # Load the TERMS tables into the terms_df dataframe
        terms_tables = db_.query('SELECT module_name, table_name FROM modules_table WHERE class_name == "TERM"')
        terms_df_list = []
        for term in terms_tables:
            entries = db_.query('SELECT * FROM ' + term.table_name)
            module = term.module_name
            df = entries.export('df')
            module_df = pd.DataFrame([module] * df.shape[0], columns=["Module"])
            df = pd.concat([module_df, df], axis=1)
            if do_print:
                print(df.columns)
                print(df.shape)
            terms_df_list.append(df)

        terms_df = pd.concat(terms_df_list)

        if do_print:
            print("\nSize of TERMS dataframe {}".format(terms_df.shape))

        # Append the linear_objective if any
        if mosdex_problem["linear_objective"] is not None:
            objective_df = pd.DataFrame(mosdex_problem["linear_objective"])
            terms_df = pd.concat([terms_df, objective_df])

            if do_print:
                print("\nSize of TERMS dataframe {}".format(terms_df.shape))

        # Now add the data to linear_expressions
        if do_print:
            print("\nLinear Expressions:")

        for r in linear_expressions:
            if do_print:
                print("\t{} {} ".format(r.module, r.variable))

            # Select the rows in terms_df for the module / dependent variable
            mask_m = terms_df["Module"].values == r.module
            mask_v = terms_df["Name"].values == r.variable
            mask = [m and v for m, v in zip(mask_m, mask_v)]

            # upload
            terms_df[mask].to_sql("linear_expressions", con=db_.get_engine(), if_exists='append', index=False)


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

    initialize_mosdex(mosdexProblem, do_print=True)
    process_algorithm(mosdexProblem, do_print=False)

    # Commence generation of base structure
    initialize_tables(mosdexProblem)
    populate_independents(mosdexProblem, do_print=False)
    populate_dependents(mosdexProblem, do_print=False)
    populate_expressions(mosdexProblem, do_print=False)

    # List the tables
    print("\n***List the Tables***")
    db = mosdexProblem['db']
    print("\n**{}**".format("Modules"))
    print(db.query('SELECT * FROM modules_table').dataset)
    print("\n**{}**".format("Metadata"))
    print(db.query('SELECT * FROM metadata_table').dataset)
    print("\n**{}**".format("Independent Variables (Columns)"))
    print(db.query('SELECT * FROM independent_variables').dataset)
    print("\n**{}**".format("Dependent Variables (Rows)"))
    print(db.query('SELECT * FROM dependent_variables').dataset)
    print("\n**{}**".format("Linear Expressions (Matrix Entries)"))
    print(db.query('SELECT * FROM linear_expressions').dataset)
    # for table in db.get_table_names():
    #     print("\n**{}**".format(table))
    #     print(db.query('SELECT * FROM ' + table).dataset)

    # Look at KEYS
    print("\n**{}**".format("KEYS"))
    keys = db.query('SELECT module_name, item_name, name FROM metadata_table WHERE key_type == "KEY"')
    for key in keys:
        key_string = "_".join([key['module_name'], key['item_name'], key['name']])
        print("\n\t{:15s} {}".format("KEY:", key_string))
        print("\t{:15s}".format("DEPENDENCIES:"))
        where_clause = ' WHERE key_type == "FOREIGN_KEY" AND source == "' + key_string + '"'
        foreign_keys = db.query('SELECT module_name, item_name, class_name FROM metadata_table ' + where_clause)
        for fkey in foreign_keys:
            fkey_string = "_".join([fkey['module_name'], fkey['item_name']])
            print("\t{:15s} {:15s} \t({})".format(" ", fkey_string, fkey["class_name"]))
