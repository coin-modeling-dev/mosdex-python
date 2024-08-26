# from records import Database

from sqlalchemy import func, DateTime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


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
