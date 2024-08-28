# from records import Database
import pandas as pd
from sqlalchemy import func, DateTime, create_engine, Engine, ForeignKey, JSON, Table, Column, Integer, Double
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

class MosdexDB:

    engine: Engine

    def __init__(self, db_endpoint: str, echo: bool = False, drop_all: bool = False):
        # Create engine
        self.engine = create_engine(db_endpoint, echo=echo)

        # Initialize MosdexBase
        if drop_all:
            MosdexBase.metadata.drop_all(self.engine)
        MosdexBase.metadata.create_all(self.engine)

    def create_Table(self, table_name, schema_dict: dict) -> None:
        metadata = MosdexBase.metadata

        # Create a new table with only the id column
        new_table = Table(
            table_name,
            metadata,
            Column('id', Integer, primary_key=True),
        )

        # Generate a dataframe with the arrays as columns
        schema_df = pd.DataFrame.from_dict(schema_dict, orient='columns')

        # Each row of the dataframe has the column definitions
        for row in range(schema_df.shape[0]):
            field_dict = dict(schema_df.iloc[row])
            if field_dict['KEYS'] is "KEY":
                new_table.append_column(Column(field_dict['name'], Integer, primary_key=True))
            elif field_dict['KEYS'] is "VALUE" and field_dict['KIND'] is "DOUBLE":
                new_table.append_column(Column(field_dict['name'], Double))




class MosdexBase(DeclarativeBase):
    pass

class MosdexFile(MosdexBase):
    __tablename__: str = "mosdex_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    syntax: Mapped[str]
    file: Mapped[str]
    date = mapped_column(DateTime, server_default=func.now())
    tag: Mapped[str]

    def __repr__(self) -> str:
        return (f"MosdexFile(id={self.id!r}, "
                f"schema={self.syntax!r}, "
                f"file={self.file!r}, "
                f"time={self.date!r}, "
                f"tag={self.tag!r})"
                )

class MosdexModule(MosdexBase):
    __tablename__ = "mosdex_modules"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("mosdex_files.id"))
    module_name: Mapped[str]
    module_class: Mapped[str]
    module_kind: Mapped[str]
    data = mapped_column(JSON)

    def __repr__(self) -> str:
        return (f"MosdexModule(id={self.id!r}, "
                f"file_id={self.parent_id!r}, "
                f"name={self.module_name!r}, "
                f"class={self.module_class!r}, "
                f"kind={self.module_kind!r})")

class MosdexTable(MosdexBase):
    __tablename__ = "mosdex_tables"

    id: Mapped[int] = mapped_column(primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("mosdex_modules.id"))
    table_name: Mapped[str]
    table_class: Mapped[str]
    table_kind: Mapped[str]
    data = mapped_column(JSON)

    def __repr__(self) -> str:
        return (f"MosdexTable(id={self.id!r}, "
                f"module_id={self.module_id!r}, "
                f"name={self.table_name!r}, "
                f"class={self.table_class!r}, "
                f"kind={self.table_kind!r})")
