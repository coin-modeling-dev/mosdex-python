from sqlalchemy import Integer, String, Double, ForeignKey
from sqlalchemy.orm import declarative_base, mapped_column

Base = declarative_base()


class MosdexTable(Base):
    __abstract__ = True  # This prevents SQLAlchemy from treating it as a database model directly

    @classmethod
    def apply_schema(cls, table_metadata):
        """Creates table class dynamically from given schema details"""

        name = table_metadata['NAME']
        kind = table_metadata['KIND']
        class_name = table_metadata['CLASS']
        schema = table_metadata['SCHEMA']

        table_name = name + '_' + class_name + '_' + kind

        # Dynamically define column mappings
        columns = {
            '__tablename__': name,
            'id': mapped_column(Integer, primary_key=True)  # Add auto-incrementing ID
        }

        for col_name, kind in zip(schema['NAME'], schema['KIND']):
            if kind == "INTEGER":
                col_type = Integer
            elif kind == "DOUBLE":
                col_type = Double
            elif kind == "STRING":
                col_type = String
            else:
                raise ValueError(f"Unsupported type {kind} for {name}")

        # Add column to schema
        columns[col_name] = mapped_column(col_type)

        return type(f"Mosdex{name}Table", (cls,), columns)

    def process_instance(self, instance_data):
        """Handles INSTANCE directive and data insertion"""

        # Get a reference to the dynamically created table class
        mosdex_table = self.__class__.apply_schema(self)
        session = Session()  # Assuming you have a SQLAlchemy Session defined

        row = mosdex_table(**instance_data)  # Create an instance of the dynamically generated model with the provided data
        session.add(row)  # Add it to the current transaction
        session.commit()


    def process_query(self, query):
        """Handles QUERY directive"""

        # Get a reference to the dynamically created table class
        mosdex_table = self.__class__.apply_schema(self)

        result = session.execute(query).fetchall()  # Execute your SQL query and get all results in one go
        for row in result:
            print(row['column_name'])  # Assuming you have a 'column_name' column, otherwise change accordingly

        def process_instance(self, instance_data, engine):
            import pandas as pd
            from sqlalchemy.orm import Session

            # Create DataFrame
            col_names = self.table_schema['NAME']
            data_df = pd.DataFrame(instance_data, columns=col_names)

            # Insert into the table
            with Session(engine) as session:
                data_df.to_sql(name=self.__tablename__, con=session.connection(), if_exists="append", index=False)
                session.commit()

