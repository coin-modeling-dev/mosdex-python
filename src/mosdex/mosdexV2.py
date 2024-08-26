from src.mosdex.mosdex_base import MosdexObject
from src.mosdex.mosdex_classes import MosdexModules, mosdex_new_object



class MosdexV2(dict):
    """
    Instance of MosdexV2 created by MosdexV2Factory.
    """
    module_list: list[MosdexObject] = []
    modules: MosdexModules
    syntax: str

    def __init__(self, mosdex_json: dict):
        """
        Constructor for instance of MosdexV2:
        - Processes the top-level objects in parameter mosdex_json.
        - Binds instance of MosdexDatabase to MosdexV2 instance.

        :param mosdex_json: A validated instance of MosdexV2 schema.
        :param mosdex_db: An instance of MosdexDatabase.
        """
        super().__init__(mosdex_json)


        # Process top-level items
        for top_item in self.keys():
            if top_item == "SYNTAX":
                self.syntax = self["SYNTAX"]

            if top_item == "MODULES":
                for item in self["MODULES"]:
                    type_tuple = (item["CLASS"], item["KIND"])
                    module_object = mosdex_new_object(type_tuple, item)
                    self.module_list.append(module_object)

        self.modules = MosdexModules(self.module_list)

    def get_syntax(self):
        return self.syntax

    def get_modules(self):
        return self.modules


