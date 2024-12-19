from sqlalchemy import Integer, String, Double, ForeignKey
from sqlalchemy.orm import declarative_base, mapped_column

Base = declarative_base()


class MosdexTable(Base):
    __abstract__ = True  # This prevents SQLAlchemy from treating it as a database model directly

    id = mapped_column(Integer, primary_key=True)  # Common column for all tables

    def __init__(self, table_metadata: dict):
        self.table_instance_name = table_metadata['NAME']
        self.table_schema = table_metadata['SCHEMA']
        self.mosdex_class = table_metadata['CLASS']
        self.mosdex_kind = table_metadata['KIND']

    @classmethod
    def from_schema(cls, table_metadata):
        """Creates table class dynamically from given schema details"""
        name = table_metadata['NAME']
        schema = table_metadata['SCHEMA']

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
                raise ValueError(f"Unsupported type {kind}")

            # Add column to schema
            columns[col_name] = mapped_column(col_type)

        return type(f"Mosdex{name}Table", (cls,), columns)

    def process_instance(self, data):
        """Handles INSTANCE directive and data insertion"""
        pass

    def process_query(self, query):
        """Handles QUERY directive"""
        pass