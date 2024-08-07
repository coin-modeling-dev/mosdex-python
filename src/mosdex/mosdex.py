import pandas as pd
import json
import os
import pprint
from jsonschema import Draft7Validator
from records import Database


class MosdexDatabase(Database):

    def __init__(self, db_file_or_url):
        super().__init__(db_file_or_url)

    def get_engine(self):
        return self._engine


class Mosdex:

    def __init__(self, schema, problem, db_file_or_url):
        self.json = None
        self.schema_file = schema
        self.problem_file = problem
        self.db = MosdexDatabase(db_file_or_url)
        self.linear_objective = []

    def mosdex_open_and_test(self, do_print=False):
        problem_file = self.problem_file
        schema_file = self.schema_file
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
        self.json = problem_json
        self.is_valid = valid

    mosdex_static_members = ["SYNTAX", "CLASS", "HEADING", "NAME", "DEPENDS", "ALGORITHM", "INITIALIZE"]
    mosdex_types = ["INPUT", "OUTPUT"]


    def mosdex_recipe(self, recipe: list, do_print=False):
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


    def mosdex_depends(self, mosdex_entity: dict, do_print=False):
        if "DEPENDS" in mosdex_entity.keys():
            if do_print:
                print("{:12s} {}".format("DEPENDS", mosdex_entity["DEPENDS"]))
            return mosdex_entity["DEPENDS"]
        else:
            return None


    def mosdex_members(self, mosdex_entity: dict, mosdex_class=None, do_print=False) -> dict:
        if mosdex_class is None:
            mosdex_classes = set([mosdex_entity[k_]["CLASS"] for k_ in mosdex_entity
                                  if k_ not in self.mosdex_static_members])
        else:
            mosdex_classes = [mosdex_class]

        members_ = {}
        for m1 in mosdex_classes:
            members_[m1] = {}
            for k1, v in mosdex_entity.items():
                if k1 not in self.mosdex_static_members and mosdex_entity[k1]["CLASS"] == m1:
                    members_[m1][k1] = v
            if do_print:
                print("{:12s} {}".format(m1, list(members_[m1].keys())))
        return members_


    def process_algorithm(self, do_print: bool = False):
        # Get the top-level members by class
        members = self.mosdex_members(self.json)

            # First, initialize the algorithm
        if "ALGORITHM" in members:
            mosdex_algorithm = members["ALGORITHM"]
        else:
            mosdex_algorithm = {"initialize_only": {"INITIALIZE": members["MODULE"].keys()}}

        # Execute the algorithm
        for name_, alg_ in mosdex_algorithm.items():
            print("**** Executing {} ****".format(name_))

            # Initialize
            self.process_initialize(module_list=alg_["INITIALIZE"], do_print=do_print)


    def process_recipe(self, mod_name, tab_name, do_print=True):
        mosdex_db = self.db
        table_name = mod_name + '_' + tab_name
        recipe_array = self.json[mod_name][tab_name]['RECIPE']

        sql_list = []
        for recipe in recipe_array:
            sql_list.append(recipe['DIRECTIVE'])
            sql_list.append(','.join(str(e) for e in recipe['PREDICATE']))

        sql_string = ' '.join(str(e) for e in sql_list)
        create_string = "CREATE TABLE " + table_name + ' AS ' + sql_string
        if do_print:
            print("\t\t\tRECIPE {}".format(create_string))

        mosdex_db.query(create_string)


    def process_initialize(self, module_list=None, do_print=False):
        mosdex_db = self.db

        if module_list is None:
            module_list = [k_ for k_ in self.json if k_ in self.json.keys()
                           and self.json[k_]['CLASS'] == 'MODULE']

        for module_name in module_list:
            module = self.json[module_name]
            if do_print:
                print("\n\tModule {}".format(module_name))

            if "INITIALIZE" in module:
                init_sequence = module["INITIALIZE"]
            else:
                init_sequence = [k_ for k_ in module.keys() if k_ not in self.mosdex_static_members]

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
                    self.process_recipe(module_name, item, do_print=do_print)
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


    def initialize_database(self, do_print=False):
        db = self.db

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



    def initialize_mosdex(self, do_print=False):

        # Initialize database and counters
        self.initialize_database(do_print=do_print)

        # Open and test the mosdex problem against the schema
        self.mosdex_open_and_test(do_print=do_print)

    def initialize_tables(self):
        db_ = self.db

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

    def populate_independents(self, do_print=False):
        db_ = self.db

        # Get list of independent variables
        sql = 'SELECT module_name, item_name, class_name, type_name, table_name ' \
              'FROM modules_table WHERE class_name is "VARIABLE"'

        independent_variables = db_.query(sql)

        if do_print:
            print("\n{}:".format("Independent Variables"))
            for r in independent_variables:
                print("\t{}\t{}\t{}\t{}\t{}".format(r.module_name, r.item_name, r.class_name,
                                                    r.table_name, r.type_name))

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
                    self.linear_objective.append({"Module": module, "Name": "OBJECTIVE",
                                                  "Name": r1.Name, "Coefficient": r1.Objective})


    def populate_dependents(self, do_print=False):
        db_ = self.db

        # Get list of dependent variables
        sql = 'SELECT module_name, item_name, class_name, type_name, table_name ' \
              'FROM modules_table WHERE class_name is "CONSTRAINT"'

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

        if self.linear_objective is not None:
            lin_obj = self.linear_objective
            modules = []
            for coeff in lin_obj:
                modules.append(coeff["Module"])
            for m_ in set(modules):
                db_.query('INSERT INTO dependent_variables (module, variable, '
                          'type, lower_bound, upper_bound) '
                          'VALUES(:m, :v, :t, :l , :u) ',
                          m=m_, v="OBJECTIVE", t="LINEAR", l="infinity", u="infinity")


    def populate_expressions(self, do_print=False):
        db_ = self.db

        # Linear Expressions
        linear_expressions = db_.query('SELECT module, variable FROM dependent_variables WHERE type is "LINEAR"')

        if linear_expressions is not None:

            # Drop the linear_expressions table
            db_.query('DROP TABLE IF EXISTS linear_expressions')

            # Load the TERMS tables into the terms_df dataframe
            terms_tables = db_.query('SELECT module_name, table_name FROM modules_table WHERE class_name is "TERM"')
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
            if self.linear_objective is not None:
                objective_df = pd.DataFrame(self.linear_objective)
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
                self.upload_dataframe(terms_df[mask], "linear_expressions")

    def get_table_names(self):
        return self.db.get_table_names()

    def export_table(self, table_name, format_type: str):
        """
        Mosdex export table in desired format.
        - csv: comma-separated value
        - yaml: yet another modeling language
        - json: Java simple object notation
        - df: Pandas dataframe
        :param table_name:
        :param format_type: one of 'csv', 'yaml', 'json', 'df'
        :return: In case of csv, yaml, or json: string
                 In case of df: a dataframe object
        """
        sql = "SELECT * FROM " + table_name
        rows_ = self.db.query(sql)
        return rows_.export(format_type)

    def print_table(self, table_name: str):
        sql = "SELECT * FROM " + table_name
        rows = self.db.query(sql)
        print(rows.dataset)

    def upload_dataframe(self, df, to_table):
        df.to_sql(to_table, con=self.db.get_engine(), if_exists='append', index=False)


if __name__ == "__main__":


    # Provide the file and schema locations
    file_dir = "data"
    problem_file = os.path.join(file_dir, "sailco_1.3-ajk.json")
    schema_dir = "data"
    schema_file = os.path.join(schema_dir, "MOSDEXSchemaV1-3-ajk.json")
    records_db = 'sqlite://'

    mosdexProblem = Mosdex(schema=schema_file, problem=problem_file, db_file_or_url=records_db)



    mosdexProblem.initialize_mosdex(do_print=True)
    mosdexProblem.process_algorithm(do_print=False)

    # Commence generation of base structure
    mosdexProblem.initialize_tables()
    mosdexProblem.populate_independents(do_print=False)
    mosdexProblem.populate_dependents(do_print=False)
    mosdexProblem.populate_expressions(do_print=False)

    # List the tables
    print("\n***List the Tables***")
    print(mosdexProblem.get_table_names())

    # Print the metadata_table
    print("\n***Print the Metadata table***")
    mosdexProblem.print_table("metadata_table")

    # Get dataframes for the variables and expressions
    df_independent_variables = mosdexProblem.export_table("independent_variables", 'df')
    df_dependent_variables = mosdexProblem.export_table("dependent_variables", 'df')
    df_linear_expressions = mosdexProblem.export_table("linear_expressions", 'df')

    # Get the metadata dataframe
    df_metadata = mosdexProblem.export_table("metadata_table", 'df')

    """
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
            
    """
