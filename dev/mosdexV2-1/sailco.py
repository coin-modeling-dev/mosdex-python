import json
import pprint

from jsonschema.validators import Draft7Validator

"""
Open a Mosdex file and validate it against the schema
"""

MOSDEX_SCHEMA_FILE = "MOSDEXSchemaV2-1.json"
MOSDEX_FILE = "sailco_2-1.json"

with open(MOSDEX_SCHEMA_FILE, "r") as f:
    schema = json.load(f)
validator = Draft7Validator(schema)

with open(MOSDEX_FILE, "r") as f:
    mosdex = json.load(f)

if not validator.is_valid(mosdex):
    print(f"File {MOSDEX_FILE} is not a valid Mosdex file.")
    pp = pprint.PrettyPrinter(indent=4)
    for error in sorted(validator.iter_errors(mosdex), key=str):
        print()
        pp.pprint(error.message)
else:
    print(f"File {MOSDEX_FILE} is a valid instance of schema {MOSDEX_SCHEMA_FILE}.")

# Get reference to a module that has KIND == MODEL
model = {}
for module in mosdex["MODULES"]:
    if module["KIND"] == "MODEL":
        model = module
        break

print(f"Got handle to MODEL: {model['NAME']}")
print(f"The sections of the model are {list(model.keys())}")
print(f"\tNAME: {model['NAME']}")
print(f"\tCLASS: {model['CLASS']}")
print(f"\tKIND: {model['KIND']}")
print(f"\tTABLES: there are {len(model['TABLES'])} tables:")
for table in model["TABLES"]:
    print(f"\t\t{table['NAME']:10s} \t class/kind: {table['CLASS']}/{table['KIND']}")
"""
Initialize the database engine
"""
from sqlalchemy import Double, ForeignKey, Integer, String, create_engine

engine = create_engine("sqlite:///:memory:")

from sqlalchemy.orm import declarative_base, mapped_column

Base = declarative_base()
Base.metadata.drop_all(bind=engine)

# Initialize the Stages, Constraints, Variables, and Matrix tables
db_tables = {}
for key in ["variables", "constraints", "matrix"]:
    db_tables[key] = {}
    db_tables[key]["table_instance_name"] = key
    db_tables[key]["table_class_name"] = model["NAME"].capitalize() + key.capitalize()
    table_attr = {
        "__tablename__": db_tables[key]["table_instance_name"],
        "id": mapped_column(Integer, primary_key=True),
        "state": mapped_column(
            String,
        ),
    }
    db_tables[key]["table_class"] = type(
        db_tables[key]["table_class_name"], (Base,), table_attr
    )

# Initialize each model table
for table_ in model["TABLES"]:
    # record table metadata in db_tables
    key = table_["NAME"]
    db_tables[key] = {}
    db_tables[key]["table_instance_name"] = key
    db_tables[key]["table_class_name"] = model["NAME"].capitalize() + key.capitalize()

    # mosdex metadata
    db_tables[key]["mosdex_json"] = table_
    db_tables[key]["mosdex_schema"] = table_["SCHEMA"]
    db_tables[key]["mosdex_class"] = table_["CLASS"]
    db_tables[key]["mosdex_kind"] = table_["KIND"]

    # local variables
    table_name = db_tables[key]["table_instance_name"]
    table_schema = db_tables[key]["mosdex_schema"]

    # INPUTS don't have stage columns
    if db_tables[key]["mosdex_kind"] == "INPUT":
        table_attr = {
            "__tablename__": table_name,
            "id": mapped_column(Integer, primary_key=True),
        }
    # VARIABLE, CONSTRAINT, and MATRIX do have stage columns
    if db_tables[key]["mosdex_class"] in ["VARIABLE", "CONSTRAINT", "MATRIX"]:
        table_attr = {
            "__tablename__": table_name,
            "id": mapped_column(Integer, primary_key=True),
        }

    # Apply the SCHEMA
    for name, kind in zip(table_schema["NAME"], table_schema["KIND"]):
        # Column type
        if kind == "INTEGER":
            type_col = Integer
        elif kind == "DOUBLE" or kind == "DOUBLE_FUNCTION":
            type_col = Double
        elif kind == "STRING":
            type_col = String
        else:
            print(
                f"Error, type {kind} is not supported.  Detected in Table {table_name}"
            )
            break

        # Relationships
        # - primary_key flag
        # - Foreign Key relationship
        if "KEYS" in table_schema and name in table_schema["KEYS"]:
            # Primary Key
            table_attr[name] = mapped_column(type_col, primary_key=True)
        if "FOREIGN_KEYS" in table_schema and name in table_schema["FOREIGN_KEYS"]:
            # Foreign Key
            f_key = table_schema["FOREIGN_KEYS"][name]
            table_attr[name] = mapped_column(type_col, ForeignKey(f_key))
        else:
            table_attr[name] = mapped_column(type_col)

    # Declarative instantiation of the table
    db_tables[key]["table_class"] = type(
        db_tables[key]["table_class_name"], (Base,), table_attr
    )


Base.metadata.create_all(
    engine,
)

print("Database tables created")
for table in Base.metadata.tables.keys():
    print(f"\t{table}")
    print(f"\t\t{Base.metadata.tables[table].columns.keys()}")

from prettytable import PrettyTable
from sqlalchemy import Table, text
from sqlalchemy.orm import Session

"""
Load the INSTANCES
"""
import numpy as np
import pandas as pd

for key in db_tables.keys():
    # Not a mosdex object
    if "mosdex_json" not in db_tables[key]:
        continue

    # Load INSTANCE
    if "INSTANCE" in db_tables[key]["mosdex_json"]:
        # Get column names
        col_names = db_tables[key]["mosdex_schema"]["NAME"]

        # Create a dataframe from the INSTANCE arrays
        data_df = pd.DataFrame(
            np.vstack(db_tables[key]["mosdex_json"]["INSTANCE"]), columns=col_names
        )
        print("\n>>DATAFRAME<< ")
        print(data_df.head())

        # Push the dataframe to the table
        with Session(engine) as session, session.begin():
            table_name = db_tables[key]["table_instance_name"]
            data_df.to_sql(
                name=table_name,
                con=session.connection(),
                if_exists="append",
                index=False,
            )
            session.flush()
            stmt = "select * from " + table_name

            rows = session.execute(text(stmt))
            pretty_table = PrettyTable()
            pretty_table.field_names = data_df.columns
            for row in rows:
                pretty_table.add_row(row[1:])
            print(pretty_table)
    else:
        # Load in another way
        pass


"""
Process VARIABLES
"""

for key in db_tables.keys():
    if "mosdex_json" not in db_tables[key]:
        continue
    if "VARIABLE" == db_tables[key]["mosdex_json"]["CLASS"]:
        for statement in db_tables[key]["mosdex_json"]["QUERY"]:
            insert_array = db_tables[key]["mosdex_schema"]["NAME"]
            select_array = statement["SELECT"]
            from_array = statement["FROM"]

            insert_stmt = "INSERT INTO " + key + "(" + ",".join(insert_array) + ")"
            select_stmt = "SELECT " + ",".join(select_array)
            from_stmt = "FROM " + ",".join(from_array)
            stmt = insert_stmt + " " + select_stmt + " " + from_stmt
            # print(stmt)
            with Session(engine) as session, session.begin():
                session.execute(text(stmt))

        with Session(engine) as session:
            stmt = "select * from " + db_tables[key]["table_instance_name"]
            rows = session.execute(text(stmt)).fetchall()
            print(f"\n>>TABLE<< {db_tables[key]['table_instance_name']}")
            print(f"{Base.metadata.tables[key].columns.keys()}")
            for row in rows:
                print(row)


"""
Process CONSTRAINTS
"""

for key in db_tables.keys():
    if "mosdex_json" not in db_tables[key]:
        continue
    if "CONSTRAINT" == db_tables[key]["mosdex_json"]["CLASS"]:
        for statement in db_tables[key]["mosdex_json"]["QUERY"]:
            insert_array = db_tables[key]["mosdex_schema"]["NAME"]
            select_array = statement["SELECT"]
            from_array = statement["FROM"]

            insert_stmt = "INSERT INTO " + key + "(" + ",".join(insert_array) + ")"
            select_stmt = "SELECT " + ",".join(select_array)
            from_stmt = "FROM " + ",".join(from_array)

            stmt = insert_stmt + " " + select_stmt + " " + from_stmt
            if "JOIN" in statement:
                join_array = statement["JOIN"]
                stmt = stmt + " JOIN " + " JOIN ".join(join_array)

            if "WHERE" in statement:
                where_array = statement["WHERE"]
                stmt = stmt + " WHERE " + " ".join(where_array)
            # print(stmt)
            with Session(engine) as session, session.begin():
                session.execute(text(stmt))

        with Session(engine) as session:
            stmt = "select * from " + db_tables[key]["table_instance_name"]
            rows = session.execute(text(stmt)).fetchall()
            print(f"\n>>TABLE<< {db_tables[key]['table_instance_name']}")
            print(f"{Base.metadata.tables[key].columns.keys()}")
            for row in rows:
                print(row)


"""
Process MATRIX
"""

for key in db_tables.keys():
    if "mosdex_json" not in db_tables[key]:
        continue
    if "MATRIX" == db_tables[key]["mosdex_json"]["CLASS"]:
        for statement in db_tables[key]["mosdex_json"]["QUERY"]:
            insert_array = db_tables[key]["mosdex_schema"]["NAME"]
            select_array = statement["SELECT"]
            from_array = statement["FROM"]

            insert_stmt = "INSERT INTO " + key + "(" + ",".join(insert_array) + ")"
            select_stmt = "SELECT " + ",".join(select_array)
            from_stmt = "FROM " + ",".join(from_array)
            stmt = insert_stmt + " " + select_stmt + " " + from_stmt

            if "JOIN" in statement:
                join_array = statement["JOIN"]
                join_stmt = " JOIN " + " JOIN ".join(join_array)
                stmt = stmt + join_stmt

            if "WHERE" in statement:
                where_array = statement["WHERE"]
                stmt = stmt + " WHERE " + " ".join(where_array)

            # print(stmt)
            with Session(engine) as session, session.begin():
                session.execute(text(stmt))

        with Session(engine) as session:
            stmt = "select * from " + db_tables[key]["table_instance_name"]
            rows = session.execute(text(stmt)).fetchall()
            print(f"\n>>TABLE<< {db_tables[key]['table_instance_name']}")
            print(f"{Base.metadata.tables[key].columns.keys()}")
            for row in rows:
                print(row)

"""
Print ctInvMat table
"""


table = Table("ctInvMat", Base.metadata, autoload_with=engine)

stmt = "SELECT period, row, invCol, invCoeff, LaginvCol, LaginvCoeff FROM ctInvMat"

# Execute a query and fetch results
with engine.connect() as connection:
    result = connection.execute(text(stmt))

# Create a PrettyTable object
pretty_table = PrettyTable()
pretty_table.field_names = ["period", "row", "col1", "coeff1", "col2", "coeff2"]

# Add rows to the PrettyTable
for row in result:
    # print(row)
    pretty_table.add_row(row)

print("stuff")
# Print the table
print(pretty_table)
# Print the table

"""
Print inventory row table
"""


table = Table("ctinv", Base.metadata, autoload_with=engine)

stmt = "SELECT period, row, sense, RHS FROM ctinv"

# Execute a query and fetch results
with engine.connect() as connection:
    result = connection.execute(text(stmt))

# Create a PrettyTable object
pretty_table = PrettyTable()
pretty_table.field_names = ["period", "row", "sense", "RHS"]

# Add rows to the PrettyTable
for row in result:
    # print(row)
    pretty_table.add_row(row)

print("stuff")
# Print the table
print(pretty_table)
# Print the table


# %%
