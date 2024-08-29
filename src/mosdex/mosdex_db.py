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
        self.metadata = MosdexBase.metadata

        # Initialize MosdexBase
        if drop_all:
            self.metadata.drop_all(self.engine)
        self.metadata.create_all(self.engine)


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
