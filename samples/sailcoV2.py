import os

from src.mosdex.mosdexV2Factory import MosdexV2Factory
from src.mosdex.mosdex_database import MosdexDatabase

# Mosdex schema and data locations
DATA_DIR = "../data"

# Initialize MosdexV2
schema_file = os.path.join(DATA_DIR, "MOSDEXSchemaV2-0.json")
db_endpoint = 'sqlite://'
mosdexV2 = MosdexV2Factory(schema_file, MosdexDatabase(db_endpoint))

# Create sailco data
sailco_file = os.path.join(DATA_DIR, "sailco_2-0.json")
sailcoV2 = mosdexV2.from_file(sailco_file)

# Print syntax
print(sailcoV2.get_syntax())

# Get modules
sailco_modules = sailcoV2.get_modules()

# Get the sailco model and print metadata
sailco_model = sailco_modules.get('sailco')
print("Model metadata:")
sailco_model.print_metadata()

# Get the sailco model tables and print metadata
sailco_tables = sailco_model.get_tables()
print("INPUT tables:")
for table in sailco_tables:
    if table.get("KIND") == "INPUT":
        table.print_metadata()
        print()


