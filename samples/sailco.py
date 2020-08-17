from records import Database
import os
from src.mosdex.mosdex import Mosdex

# Provide the file and schema locations
schema_dir = "../data"
file_dir = "../data"
problem_file = os.path.join(file_dir,"sailco_1.3-ajk.json")
schema_file = os.path.join(schema_dir,"MOSDEXSchemaV1-3-ajk.json")
records_db = 'sqlite://'

# Initialize mosdex problem
mosdex = Mosdex(schema_file, problem_file, records_db)

# Parse the MOSDEX file
mosdex.initialize_mosdex(do_print=True)
mosdex.process_algorithm()

# Generate base structures
mosdex.initialize_tables()
mosdex.populate_independents()
mosdex.populate_dependents()
mosdex.populate_expressions()

# List the tables
print("\n***List the Tables***")
db: Database = mosdex.db
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
