# from records import Database
import json

from sqlalchemy import func, DateTime, create_engine, Engine, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
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
        return (f"MosdexObject(id={self.id!r}, "
                f"file_id={self.parent_id!r}, "
                f"object_name={self.module_name!r}, "
                f"object_class={self.module_class!r}, "
                f"object_kind={self.module_kind!r})")
