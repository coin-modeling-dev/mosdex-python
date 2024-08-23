import os
from src.mosdex.mosdexV1 import Mosdex

# Provide the file and schema locations
schema_dir = "../data"
file_dir = "../data"
problem_file = os.path.join(file_dir,"sailco_2-0.json")
schema_file = os.path.join(schema_dir,"MOSDEXSchemaV2-0.json")
records_db = 'sqlite://'

# Initialize mosdex problem
mosdex = Mosdex(schema_file, problem_file, records_db)

# Parse the MOSDEX problem file
mosdex.initialize_mosdex(do_print=True)
mosdex.process_algorithm()

# Print the dependencies driven order
print(mosdex.node_order())

# Generate base structures
mosdex.create_variable_tables()
mosdex.populate_independents()
mosdex.populate_dependents()
mosdex.populate_expressions()

# List the tables
print("\n***List the Tables***")
print(mosdex.get_table_names())

# Print the modules_table
mosdex.print_table("modules_table")

# Print the metadata_table
mosdex.print_table("metadata_table")

# Print the independent variables table
print("\n***Print the independent variables table***")
mosdex.print_table("independent_variables")

# Print the dependent variables table
print("\n***Print the dependent variables table***")
mosdex.print_table("dependent_variables")

# Print the linear expressions table
print("\n***Print the linear expressions table***")
mosdex.print_table("linear_expressions")

# Print the totalCost table
print("\n***Print the totalCost table***")
mosdex.print_table("sailco_totalCost")


