from src.mosdex.mosdex_classes import MosdexModules, MosdexModel
from src.mosdex.mosdex_database import MosdexDatabase


class MosdexData(dict):

    mosdex_db: MosdexDatabase
    modules: MosdexModules
    syntax: str

    def __init__(self, mosdex_json: dict, mosdex_db: MosdexDatabase):
        """
        MosdexData constructor. Called from MosdexV2.
        :param mosdex_json: A validated instance of MosdexV2 schema.
        :param mosdex_db: An instance of MosdexDatabase.
        """
        self.mosdex_db = mosdex_db
        super().__init__(mosdex_json)

        self.syntax = self["SYNTAX"]
        modules = []
        for item in self["MODULES"]:
            if "KIND" in item:
                modules.append(MosdexModel(item))

        self.modules = MosdexModules(modules)

    def get_syntax(self):
        return self.syntax

    def get_modules(self):
        return self.modules


