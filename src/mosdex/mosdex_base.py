from sqlalchemy.orm import Session

from src.mosdex.mosdex_db import MosdexDB, MosdexTable, MosdexModule


class MosdexObjectBase(dict):
    mosdex_db: MosdexDB
    parent_id: int
    object_id: int

    def __init__(self, mosdex_json: dict, mosdex_db: MosdexDB, parent_id: int) -> None:
        super().__init__(mosdex_json)
        self.mosdex_db = mosdex_db
        self.object_id = parent_id

    def print_metadata(self, prefix="\t"):
        print(f"{prefix}"
              f"{self.get('NAME')}, "
              f"Class: {self.get('CLASS')}, "
              f"Kind: {self.get('KIND')}")

    def set_object_id(self, object_id: int) -> None:
        self.object_id = object_id


class MosdexModuleBase(MosdexObjectBase):

    def __init__(self, mosdex_json: dict, mosdex_db: MosdexDB, parent_id: int):
        super().__init__(mosdex_json, mosdex_db=mosdex_db, parent_id=parent_id)

        # Record in MosdexModule table
        with Session(mosdex_db.engine) as session, session.begin():
            row = MosdexModule(parent_id=parent_id,
                               module_name=mosdex_json["NAME"],
                               module_class=mosdex_json["CLASS"],
                               module_kind=mosdex_json["KIND"],
                               data=mosdex_json["HEADING"]
                               )
            session.add(row)
            session.flush()
            self.object_id = row.id


class MosdexTableBase(MosdexObjectBase):
    table_name: str

    def __init__(self, mosdex_json: dict, mosdex_db:MosdexDB, parent_id: int) -> None:
        super().__init__(mosdex_json, mosdex_db, parent_id)

        with Session(mosdex_db.engine) as session, session.begin():
            row = MosdexTable(module_id=parent_id,
                              table_name=mosdex_json["NAME"],
                              table_class=mosdex_json["CLASS"],
                              table_kind=mosdex_json["KIND"],
                              schema=mosdex_json["NAME"] + "_schema",
                              data=mosdex_json["NAME"] + "_data",
                              )
            session.add(row)
            session.flush()
            self.object_id = row.id

        self.table_name = mosdex_json["NAME"]

    def get_data_table_name(self) -> str:
        return self.data_table_name

    def get_schema_table_name(self) -> str:
        return self.schema_table_name


class MosdexArrayBase(list[MosdexObjectBase]):
    # dictionary to index list[MosdexObjectBase] by NAME
    array_dict: dict

    def __init__(self, mosdex_array: list[MosdexObjectBase]):
        super().__init__(mosdex_array)
        self.array_dict = {}
        for member in mosdex_array:
            self.array_dict[member['NAME']] = member

    def get(self, name: str) -> MosdexObjectBase:
        return self.array_dict.get(name)

    def print_members_metadata(self, prefix="\t\t"):
        for member in self:
            member.print_metadata(prefix=prefix)

