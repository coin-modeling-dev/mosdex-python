def create_tables(model: dict):
    db_tables = {}

    for table_ in model['TABLES']:
        # Record table metadata
        table_metadata = {
            'NAME': table_['NAME'],
            'SCHEMA': table_['SCHEMA'],
            'CLASS': table_['CLASS'],
            'KIND': table_['KIND']
        }

        # Dynamically create table classes using MosdexTable
        db_tables[table_['NAME']] = MosdexTable.apply_schema(table_metadata)

    return db_tables