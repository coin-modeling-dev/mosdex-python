

class MosdexObject(dict):
    def __init__(self, mosdex_json: dict):
        super().__init__(mosdex_json)

    def print_metadata(self, prefix="\t"):
        print(f"{prefix}"
              f"{self.get('NAME')}, "
              f"Class: {self.get('CLASS')}, "
              f"Kind: {self.get('KIND')}")

class MosdexArray(list[MosdexObject]):
    # dictionary to index list[MosdexObject] by NAME
    array_dict: dict

    def __init__(self, mosdex_array: list[MosdexObject]):
        super().__init__(mosdex_array)
        self.array_dict = {}
        for member in mosdex_array:
            self.array_dict[member.get('NAME')] = member

    def get(self, name: str) -> MosdexObject:
        return self.array_dict.get(name)

    def print_members_metadata(self, prefix="\t"):
        for member in self:
            member.print_metadata(prefix=prefix)

