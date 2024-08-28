import pandas as pd
from sqlalchemy.orm import Session

from src.mosdex.exceptions import MosdexInvalidClassKindPairError
from src.mosdex.mosdex_base import MosdexArrayBase, MosdexObjectBase
from src.mosdex.mosdex_db import MosdexDB, MosdexModule, MosdexTable

MODULE_KINDS = {
    "MODULE": ["MODEL"]
}

TABLE_KINDS = {
    "DATA": ["INPUT", "OUTPUT"],
    "VARIABLE": ["CONTINUOUS"],
    "CONSTRAINT": ["LINEAR"],
    "TERM": ["LINEAR"],
}

def mosdex_object(mosdex_type: tuple[str, str], mosdex_json: dict, parent_id: int, mosdex_db: MosdexDB) -> MosdexObjectBase:
    """
    Method to generate a new MosdexObjectBase derived class from a (CLASS, KIND) pair.

    :param mosdex_type: tuple pair consisting of CLASS value and a KIND value.
    :param mosdex_json: input to the derived class.
    :param mosdex_db: MosdexDB object from the MosdexV2Factory.
    :param parent_id: Key in the mosdex_files table for the parent object of the current object.

    :return: MosdexObjectBase derived class.
    """
    try:
        if (mosdex_type[0] in MODULE_KINDS.keys()
                and mosdex_type[1] in MODULE_KINDS[mosdex_type[0]]):

            module_instance: dict[[str, str], MosdexObjectBase] = \
            {
                ("MODULE", "MODEL"):
                    MosdexModel(mosdex_json, parent_id=parent_id, mosdex_db=mosdex_db),
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
                module_instance[mosdex_type].set_object_id(row.id)

            return module_instance[mosdex_type]

        elif (mosdex_type[0] in TABLE_KINDS.keys()
              and mosdex_type[1] in TABLE_KINDS[mosdex_type[0]]):

            table_instance: dict[[str, str], MosdexTableBase] = {
                ("DATA", "INPUT"):
                    MosdexData(mosdex_json, parent_id=parent_id, mosdex_db=mosdex_db),
                ("DATA", "OUTPUT"):
                    MosdexData(mosdex_json, parent_id=parent_id, mosdex_db=mosdex_db),
                ("VARIABLE", "CONTINUOUS"):
                    MosdexVariable(mosdex_json, parent_id=parent_id, mosdex_db=mosdex_db),
                ("CONSTRAINT", "LINEAR"):
                    MosdexConstraint(mosdex_json, parent_id=parent_id, mosdex_db=mosdex_db),
                ("OBJECTIVE", "LINEAR"):
                    MosdexConstraint(mosdex_json, parent_id=parent_id,mosdex_db=mosdex_db),
                ("TERM", "LINEAR"):
                    MosdexTerm(mosdex_json, parent_id=parent_id, mosdex_db=mosdex_db),
            }
            with Session(mosdex_db.engine) as session, session.begin():
                row = MosdexTable(module_id=parent_id,
                                   table_name=mosdex_json["NAME"],
                                   table_class=mosdex_json["CLASS"],
                                   table_kind=mosdex_json["KIND"],
                                   data=mosdex_json
                                   )
                session.add(row)
                session.flush()
                table_instance[mosdex_type].set_object_id(row.id)

            return table_instance[mosdex_type]

        else:
            raise MosdexInvalidClassKindPairError(name=mosdex_json["NAME"],
                                          invalid_class=mosdex_type[0],
                                          kind=mosdex_type[1])
    except MosdexInvalidClassKindPairError as e:
        print(f"Object name: {e.name} has invalid class-kind pair: ({e.invalid_class}, {e.kind})")

class MosdexTableBase(MosdexObjectBase):

    def __init__(self, mosdex_json: dict, mosdex_db: MosdexDB, parent_id: int):
        super().__init__(mosdex_json, mosdex_db, parent_id)

        # Process schema, if there is one
        if "SCHEMA" in mosdex_json:
            self.schema = MosdexSchema(mosdex_json["SCHEMA"], mosdex_db=mosdex_db, object_id=self.object_id)
        else:
            self.schema = None




class MosdexSchema(MosdexObjectBase):

    def __init__(self, mosdex_json, mosdex_db: MosdexDB, object_id: int):

        schema_dict = {}
        table_keys = mosdex_json.keys()

        # Generate a dict of the arrays in Schema
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
            fields.append(MosdexField(field_dict, mosdex_db=mosdex_db, parent_id=object_id ))

        self.schema_fields = MosdexFields(fields)

    def get_schema_fields(self):
        return self.schema_fields


class MosdexModel(MosdexObjectBase):

    def __init__(self, mosdex_json: dict, mosdex_db: MosdexDB, parent_id: int):
        super().__init__(mosdex_json, mosdex_db=mosdex_db, parent_id=parent_id)

        tables = []
        for table in mosdex_json.get('TABLES'):
            table_class = table.get('CLASS')
            table_kind = table.get('KIND')
            table_object = mosdex_object( (table_class, table_kind), table,
                                          parent_id=self.object_id,
                                          mosdex_db=mosdex_db)
            tables.append(table_object)

        self.mosdex_tables = MosdexTables(tables)

    def get_tables(self):
        return self.mosdex_tables



class MosdexData(MosdexTableBase):
    pass


class MosdexField(MosdexObjectBase):
    pass

class MosdexTerm(MosdexObjectBase):
    pass

class MosdexVariable(MosdexTableBase):
    pass

class MosdexConstraint(MosdexTableBase):
    pass


class MosdexModules(MosdexArrayBase):
    pass

class MosdexTables(MosdexArrayBase):
    pass

class MosdexFields(MosdexArrayBase):
    pass
