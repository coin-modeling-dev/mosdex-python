import mosdex
from records import Database
import os

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

mosdex.read.initialize_mosdex(mosdexProblem, do_print=True)
mosdex.read.process_algorithm(mosdexProblem, do_print=False)

# Commence generation of base structure
mosdex.generate_OSI.initialize_tables(mosdexProblem)
mosdex.populate_independents(mosdexProblem, do_print=False)
mosdex.populate_dependents(mosdexProblem, do_print=False)
mosdex.populate_expressions(mosdexProblem, do_print=False)

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
# for table in db.get_table_names():
#     print("\n**{}**".format(table))
#     print(db.query('SELECT * FROM ' + table).dataset)
