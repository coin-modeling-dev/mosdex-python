import src.mosdex.read_MOSDEX as read
import src.mosdex.generate_OSI as osi
from records import Database
import os

# Provide the file and schema locations
schema_dir = "../data"
file_dir = "../data"
mosdex_problem_file = "sailco_1.3-ajk.json"
mosdex_schema_file = "MOSDEXSchemaV1-3-ajk.json"
records_db = 'sqlite://'

# Initialize mosdex problem
mosdexProblem = {'db_file': records_db,
                 'problem_file': os.path.join(file_dir, mosdex_problem_file),
                 'schema_file': os.path.join(file_dir, mosdex_schema_file)}

# Parse the MOSDEX file
read.initialize_mosdex(mosdexProblem, do_print=True)
read.process_algorithm(mosdexProblem, do_print=False)

# Generate base structures
osi.initialize_tables(mosdexProblem)
osi.populate_independents(mosdexProblem, do_print=False)
osi.populate_dependents(mosdexProblem, do_print=False)
osi.populate_expressions(mosdexProblem, do_print=False)

# List the tables
print("\n***List the Tables***")
db: Database = mosdexProblem['db']
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
