if __name__ == "__main__":
    # Load schema and mosdex JSON
    with open(MOSDEX_SCHEMA_FILE) as f:
        schema = json.load(f)
    with open(MOSDEX_FILE) as f:
        mosdex = json.load(f)

    # Validate schema
    if not Draft7Validator(schema).is_valid(mosdex):
        raise ValueError(f"{MOSDEX_FILE} is invalid")

    # Extract model details
    model = next(m for m in mosdex["MODULES"] if m["KIND"] == "MODEL")

    # Initialize database and tables
    engine = initialize_database()
    db_tables = create_tables(model)

    # Process directives
    for table_name, table_class in db_tables.items():
        table_instance = table_class()

        # Handle INSTANCE
        if "INSTANCE" in table_class.mosdex_json:
            table_instance.process_instance(table_class.mosdex_json["INSTANCE"], engine)

        # Handle QUERY
        if "QUERY" in table_class.mosdex_json:
            table_instance.process_query(table_class.mosdex_json["QUERY"], engine)