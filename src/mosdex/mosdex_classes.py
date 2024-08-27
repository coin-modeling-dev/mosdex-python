import pandas as pd
from sqlalchemy.orm import Session

from src.mosdex.mosdex_base import MosdexArrayBase, MosdexObjectBase
from src.mosdex.mosdex_db import MosdexDB, MosdexModule


def mosdex_object(mosdex_type: tuple[str, str], mosdex_json: dict, parent_id: int, mosdex_db: MosdexDB) -> MosdexObjectBase:
    """
    Method to generate a new MosdexObjectBase derived class from a (CLASS, KIND) pair.

    :param mosdex_db: MosdexDB object from the MosdexV2Factory.
    :param parent_id: Key in the mosdex_files table for the parent object of the current object.
    :param mosdex_type: tuple pair consisting of CLASS value and a KIND value.
    :param mosdex_json: input to the derived class.
    :return: MosdexObjectBase derived class.
    """

    mosdex_instance: dict[[str, str], MosdexObjectBase] = \
        {
            ("MODULE", "MODEL"):
                MosdexModel(mosdex_json, parent_id=parent_id, mosdex_db=mosdex_db),
            ("DATA", "INPUT"):
                MosdexTable(mosdex_json, parent_id=parent_id, mosdex_db=mosdex_db),
            ("DATA", "OUTPUT"):
                MosdexTable(mosdex_json, parent_id=parent_id, mosdex_db=mosdex_db),
            ("VARIABLE", "CONTINUOUS"):
                MosdexVariable(mosdex_json, parent_id=parent_id, mosdex_db=mosdex_db),
            ("CONSTRAINT", "LINEAR"):
                MosdexConstraint(mosdex_json, parent_id=parent_id, mosdex_db=mosdex_db),
            ("TERM", "LINEAR"):
                MosdexTerm(mosdex_json, parent_id=parent_id, mosdex_db=mosdex_db)
        }

    with Session(mosdex_db.engine) as session, session.begin():
        row = MosdexModule(parent_id=parent_id,
                           module_name=mosdex_json["NAME"],
                           module_class=mosdex_json["CLASS"],
                           module_kind=mosdex_json["KIND"],
                           data=mosdex_json["HEADING"]
                           )
        session.add(row)
        session.flush()
        mosdex_instance[mosdex_type].set_object_id(row.id)

    return mosdex_instance[mosdex_type]


class MosdexModules(MosdexArrayBase):
    pass

class MosdexTables(MosdexArrayBase):
    pass

class MosdexFields(MosdexArrayBase):
    pass

class MosdexSchema(MosdexArrayBase):

    # TODO: need to get the Table's object id
    def __init__(self, mosdex_json, mosdex_db: MosdexDB, object_id: int):

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
            fields.append(MosdexField(field_dict, mosdex_db=mosdex_db, ))

        super().__init__(fields)

    def print_members_metadata(self):
        print("\tSCHEMA")
        for members in self:
            members.print_metadata("\t\t")


class MosdexData(MosdexObjectBase):
    pass

class MosdexField(MosdexObjectBase):
    pass

class MosdexTable(MosdexObjectBase):

    def __init__(self, mosdex_json: dict, mosdex_db: MosdexDB, parent_id: int):
        super().__init__(mosdex_json, mosdex_db, parent_id)

        # Process schema, if there is one
        if "SCHEMA" in mosdex_json:
            self.schema = MosdexSchema(mosdex_json["SCHEMA"], mosdex_db=mosdex_db, object_id=self.object_id)
        else:
            self.schema = None

    def print_metadata(self):
        super().print_metadata()
        if self.schema is not None:
            self.schema.print_members_metadata()


class MosdexModel(MosdexObjectBase):

    mosdex_tables: MosdexTables

    def __init__(self, mosdex_json: dict, mosdex_db: MosdexDB, parent_id: int):
        super().__init__(mosdex_json, mosdex_db=mosdex_db, parent_id=parent_id)

        tables = []
        for table in mosdex_json.get('TABLES'):
            tables.append(MosdexTable(table, mosdex_db=mosdex_db, parent_id=self.object_id))

        self.mosdex_tables = MosdexTables(tables)

    def get_tables(self):
        return self.mosdex_tables

class MosdexTerm(MosdexObjectBase):
    pass

class MosdexVariable(MosdexObjectBase):
    pass

class MosdexConstraint(MosdexObjectBase):
    pass