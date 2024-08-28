from src.mosdex.mosdex_base import MosdexObjectBase
from src.mosdex.mosdex_classes import MosdexModules, mosdex_object
from src.mosdex.mosdex_db import MosdexDB


class MosdexV2(dict):
    """
    Instance of MosdexV2 created by MosdexV2Factory.
    """
    module_list: list[MosdexObjectBase] = []
    modules: MosdexModules
    syntax: str

    def __init__(self, mosdex_json: dict, file_id: int, mosdex_db: MosdexDB):
        """
        Constructor for instance of MosdexV2:
        - Processes the top-level objects in parameter mosdex_json.
        - Binds instance of MosdexDatabase to MosdexV2 instance.

        :param mosdex_json: A validated instance of MosdexV2 schema.
        :param mosdex_db: An instance of MosdexDatabase.
        """
        super().__init__(mosdex_json)

        self.file_id = file_id if isinstance(file_id, int) else int(file_id)
        self.mosdex_db = mosdex_db

        # Process MODULES
        for top_item in self.keys():
            if top_item == "MODULES":
                for item in self["MODULES"]:
                    type_tuple = (item["CLASS"], item["KIND"])
                    module_object = mosdex_object(type_tuple, item, parent_id=file_id, mosdex_db=mosdex_db)
                    self.module_list.append(module_object)

        self.modules = MosdexModules(self.module_list)

    def get_syntax(self):
        return self.syntax

    def get_modules(self):
        return self.modules


