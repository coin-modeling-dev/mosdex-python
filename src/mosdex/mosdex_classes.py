from src.mosdex.mosdex_base import MosdexArray, MosdexObject
import pandas as pd


class MosdexModules(MosdexArray):
    pass

class MosdexTables(MosdexArray):
    pass

class MosdexFields(MosdexArray):
    pass

class MosdexSchema(MosdexArray):
    def __init__(self, mosdex_json):

        schema_dict = {}
        table_keys = mosdex_json.keys()

        # Generate a dict of of the arrays in Schema
        #  - switch
        for key in table_keys:
            schema_dict[key] = mosdex_json[key]

        # Generate a dataframe with the arrays as columns
        schema_df = pd.DataFrame.from_dict(schema_dict, orient='columns')

        # Extract each row and use to initialize MosdexField
        fields = []
        for row in range(schema_df.shape[0]):
            field_dict = dict(schema_df.iloc[row])
            field_dict["CLASS"] = "FIELD"
            fields.append(MosdexField(field_dict))

        super().__init__(fields)

    def print_members_metadata(self):
        print("\tSCHEMA")
        for members in self:
            members.print_metadata("\t\t")



class MosdexField(MosdexObject):
    pass

class MosdexTable(MosdexObject):

    def __init__(self, mosdex_json: dict):
        super().__init__(mosdex_json)

        # Process schema, if there is one
        if "SCHEMA" in mosdex_json:
            self.schema = MosdexSchema(mosdex_json["SCHEMA"])
        else:
            self.schema = None

    def print_metadata(self):
        super().print_metadata()
        if self.schema is not None:
            self.schema.print_members_metadata()


class MosdexModel(MosdexObject):

    mosdex_tables: MosdexTables

    def __init__(self, mosdex_json: dict):
        super().__init__(mosdex_json)

        tables = []
        for table in mosdex_json.get('TABLES'):
            tables.append(MosdexTable(table))

        self.mosdex_tables = MosdexTables(tables)

    def get_tables(self):
        return self.mosdex_tables
