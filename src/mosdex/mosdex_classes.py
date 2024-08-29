from typing import Dict, Any

import pandas as pd
from pandas.io.sas.sas_constants import col_count_p1_multiplier
from sqlalchemy import Table, Column, Integer, Double
from sqlalchemy.orm import Session

from src.mosdex.exceptions import MosdexInvalidClassKindPairError, MosdexInvalidTableKindPairError, \
    MosdexTableSchemaNotFoundError
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

COLUMN_KINDS = {
    "VALUE": ["INTEGER", "DOUBLE"],
    "KEY": ["INTEGER"],
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



class MosdexTableBase(MosdexObjectBase):

    new_table: Table
    table_name: str
    col_names: list[str]

    def __init__(self, mosdex_json: dict, mosdex_db: MosdexDB, parent_id: int):
        super().__init__(mosdex_json, mosdex_db, parent_id)

        # Create a new sqlalchemy table with the id column
        self.table_name = mosdex_json["NAME"]
        self.new_table = Table(
            self.table_name,
            mosdex_db.metadata,
            Column('id', Integer, primary_key=True)
        )
        self.col_names = []



class MosdexData(MosdexTableBase):

    def __init__(self, mosdex_json: dict, mosdex_db: MosdexDB, parent_id: int):

        super().__init__(mosdex_json, mosdex_db, parent_id)

        try:
            if "SCHEMA" in mosdex_json:

                # Generate a dataframe with the arrays as columns
                schema_dict = mosdex_json["SCHEMA"]
                schema_df = pd.DataFrame.from_dict(schema_dict, orient='columns')
                self.col_names = schema_df.columns

                # Each row of the dataframe has the column definitions
                for row in range(schema_df.shape[0]):
                    col: dict[str, str] = dict(schema_df.iloc[row])
                    col_name = col['NAME']
                    col_kind = col['KIND']
                    col_keys = col['KEYS']

                    k = (col_keys, col_kind)
                    if k[0] in COLUMN_KINDS.keys() and k[1] in COLUMN_KINDS[k[0]]:
                        if col_keys is "KEY":
                            self.new_table.append_column(Column(col_name, Integer, primary_key=True))
                        elif col_keys is "VALUE" and col_kind is "DOUBLE":
                            self.new_table.append_column(Column(col_name, Double))
                        elif col_keys is "VALUE" and col_kind is "INTEGER":
                            self.new_table.append_column(Column(col_name, Integer))

                        else:
                            raise MosdexInvalidTableKindPairError(name=col_name, kind=col_kind, keys=col_keys)
            else:
                raise MosdexTableSchemaNotFoundError(name=mosdex_json["NAME"])

            if "INSTANCE" in mosdex_json:
                with Session(mosdex_db.engine) as session, session.begin():
                    # Add the rows
                    for values in mosdex_json["INSTANCE"]:
                        row = MosdexTable(values)
                        session.add(row)


        except MosdexInvalidTableKindPairError as e:
          print(e)

        except MosdexTableSchemaNotFoundError as e:
            print(e)


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
