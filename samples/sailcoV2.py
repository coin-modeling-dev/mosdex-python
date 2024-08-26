from src.mosdex.mosdexV2Factory import MosdexV2Factory
from src.mosdex.mosdex_database import MosdexFile
from sqlalchemy import select
from pathlib import Path

# Mosdex schema and data file
SCHEMA_FILE = "../data/MOSDEXSchemaV2-0.json"
SAILCO_FILE = "../data/sailco_2-0.json"

# Database
DATABASE = 'sqlite://'  # in-memory sqlite

# Initialize MosdexV2
mosdexV2 = MosdexV2Factory(Path(SCHEMA_FILE), DATABASE)

# Create sailco data
sailcoV2 = mosdexV2.from_file(Path(SAILCO_FILE), tag="test")

# Check the file data in the database
with mosdexV2.Session() as session:
    stmt = select(MosdexFile).where(MosdexFile.tag == "test")
    for item in session.scalars(stmt):
        print(item)

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


