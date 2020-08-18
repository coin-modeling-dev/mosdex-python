import os
from mosdex import Mosdex
import pandas

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
print(mosdex.get_table_names())

# Print the metadata_table
print("\n***Print the Metadata table***")
mosdex.print_table("metadata_table")

