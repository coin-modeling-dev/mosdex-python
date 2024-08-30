from sqlalchemy.orm import Session

from src.mosdex.mosdexV2Factory import MosdexV2Factory
from src.mosdex.mosdex_db import MosdexFile, MosdexModule
from sqlalchemy import select, desc, Table
from pathlib import Path

# Mosdex schema and data file
SCHEMA_FILE = "../data/MOSDEXSchemaV2-0.json"
SAILCO_FILE = "../data/sailco_2-0.json"

# Database
DATABASE = 'sqlite://'  # in-memory sqlite

# Initialize MosdexV2Factory
mosdexV2factory = MosdexV2Factory(schema_file=Path(SCHEMA_FILE),
                                  db_endpoint= DATABASE,
                                  echo=True,  # If True, engine logs SQL to stdout
                                  drop_all=True  # If True, database drops all tables
                                  )

# Get MosdexDB
mosdex_db = mosdexV2factory.mosdex_db

# Create sailco data
sailcoV2 = mosdexV2factory.from_file(Path(SAILCO_FILE), tag="test")

# print file record just written to MosdexFile table and get file_id
with Session(mosdex_db.engine) as session:
    stmt = select(MosdexFile).where(MosdexFile.tag.is_("test")).order_by(desc(MosdexFile.id))
    rows = session.scalars(statement=stmt)
    for row in rows:
        print(row)
        file_id = row.id

# print module records for this file
with Session(mosdex_db.engine) as session:
    stmt = select(MosdexModule).where(MosdexModule.id.is_(file_id))
    for row in session.scalars(stmt):
        print(row)


# Get modules and print the rows
sailco_modules = sailcoV2.get_modules()
for module in sailco_modules:
    with Session(mosdex_db.engine) as session:
        stmt = select(MosdexModule).where(MosdexModule.parent_id.is_(file_id))
        for row in session.scalars(stmt):
            print(row)

#

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


# Print the demands table
with Session(mosdex_db.engine) as session:
    table = Table('demands', mosdex_db.metadata, autoload=True, autoload_with=mosdex_db.engine)
    print(select(table))
