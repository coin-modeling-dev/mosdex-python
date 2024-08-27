from src.mosdex.mosdex_db import MosdexDB


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

class MosdexArrayBase(list[MosdexObjectBase]):
    # dictionary to index list[MosdexObjectBase] by NAME
    array_dict: dict

    def __init__(self, mosdex_array: list[MosdexObjectBase]):
        super().__init__(mosdex_array)
        self.array_dict = {}
        for member in mosdex_array:
            self.array_dict[member.get('NAME')] = member

    def get(self, name: str) -> MosdexObjectBase:
        return self.array_dict.get(name)

    def print_members_metadata(self, prefix="\t\t"):
        for member in self:
            member.print_metadata(prefix=prefix)

