import numpy as np
import pandas as pd
from sqlalchemy import Column, Integer, Double
from sqlalchemy.orm import Session

from src.mosdex.exceptions import MosdexInvalidType, MosdexInvalidTableKindPairError, \
    MosdexDataSchemaNotFoundError
from src.mosdex.mosdex_base import MosdexArrayBase, MosdexObjectBase, MosdexTableBase, MosdexModuleBase
from src.mosdex.mosdex_db import MosdexDB

MODULE_TYPES = [
    # Module Class-Kind pairs
    ("MODULE", "MODEL"),
]

TABLE_TYPES = [
    # Table Class-Kind pairs
    ("DATA", "INPUT"),
    ("DATA", "OUTPUT"),
    ("VARIABLE", "CONTINUOUS"),
    ("CONSTRAINT", "LINEAR"),
    ("OBJECTIVE", "LINEAR"),
    ("TERM", "LINEAR")
]
SCHEMA_TYPES = [
    # Schema Kind-Keys pairs
    ("DOUBLE", "VALUE"),
    ("INTEGER", "VALUE"),
    ("INTEGER", "KEY"),
    ("STRING", "KEY"),
]

MOSDEX_TYPES = MODULE_TYPES + TABLE_TYPES + SCHEMA_TYPES


def create_mosdex_object(mosdex_type: tuple[str, str], mosdex_json: dict, parent_id: int=0,
                         mosdex_db: MosdexDB=None) -> MosdexObjectBase:
    """
    Method to generate a new MosdexObjectBase derived class from a (CLASS, KIND) pair.

    :param mosdex_type: tuple pair consisting of CLASS value and a KIND value.
    :param mosdex_json: input to the derived class.
    :param mosdex_db: MosdexDB object from the MosdexV2Factory.
    :param parent_id: Key in the mosdex_files table for the parent object of the current object.

    :return: instance of MOSDEX_TYPE.
    """

    mosdex_instance = {}

    try:
        if mosdex_type not in MOSDEX_TYPES:
            raise MosdexInvalidType(name=mosdex_json["NAME"],
                                    invalid_type=mosdex_type
                                    )

        if mosdex_type == ("MODULE", "MODEL"):
            mosdex_instance = MosdexModel(mosdex_json, parent_id=parent_id, mosdex_db=mosdex_db)

        if mosdex_type == ("DATA", "INPUT"):
            mosdex_instance = MosdexData(mosdex_json, parent_id=parent_id, mosdex_db=mosdex_db)

        if mosdex_type == ("DATA", "OUTPUT"):
            mosdex_instance = MosdexData(mosdex_json, parent_id=parent_id, mosdex_db=mosdex_db)

        if mosdex_type == ("VARIABLE", "CONTINUOUS"):
            mosdex_instance = MosdexVariable(mosdex_json, parent_id=parent_id, mosdex_db=mosdex_db)

        if mosdex_type == ("CONSTRAINT", "LINEAR"):
            mosdex_instance = MosdexConstraint(mosdex_json, parent_id=parent_id, mosdex_db=mosdex_db)

        if mosdex_type == ("TERM", "LINEAR"):
            mosdex_instance = MosdexTerm(mosdex_json, parent_id=parent_id, mosdex_db=mosdex_db)

        if mosdex_type == SCHEMA_TYPES:
            mosdex_instance = mosdex_json

        return mosdex_instance

    except MosdexInvalidType as e:
        print(f"Object name: {e.name} has invalid mosdex type: {e.invalid_type}")
        raise


class MosdexModel(MosdexModuleBase):
    mosdex_tables: list[MosdexObjectBase] = []

    def __init__(self, mosdex_json: dict, mosdex_db: MosdexDB, parent_id: int):
        super().__init__(mosdex_json, mosdex_db=mosdex_db, parent_id=parent_id)

        # Process TABLES
        for table in mosdex_json.get('TABLES'):
            table_class = table.get('CLASS')
            table_kind = table.get('KIND')
            table_object = create_mosdex_object((table_class, table_kind), table,
                                                parent_id=self.object_id,
                                                mosdex_db=mosdex_db)
            self.mosdex_tables.append(table_object)

    def get_tables(self):
        return self.mosdex_tables


class MosdexData(MosdexTableBase):

    def __init__(self, mosdex_json: dict, mosdex_db: MosdexDB, parent_id: int):

        super().__init__(mosdex_json, mosdex_db, parent_id)

        # Data will be loaded into a dataframe
        # then pushed to table using df.to_sql()
        col_dtype = {}

        try:
            if "SCHEMA" in mosdex_json:

                # Create dataframe with schema arrays as rows
                schema_df = pd.DataFrame.from_dict(mosdex_json["SCHEMA"], orient='columns')
                print(schema_df)

            if "INSTANCE" in mosdex_json:

                # Create the dataframe from the INSTANCE arrays
                data_df = pd.DataFrame(np.vstack(mosdex_json['INSTANCE']), columns=list(col_dtype.keys()))

                # Push the dataframe to the table
                with Session(mosdex_db.engine) as session, session.begin():
                    data_df.to_sql(name=self.table_name, con=session.connection(), if_exists='append',
                                   index=False, dtype=col_dtype)
                    session.flush()
                    stmt = self.new_table.select()
                    for row in session.scalars(stmt):
                        print(row)

        except MosdexInvalidTableKindPairError as e:
            print(e)

        except MosdexDataSchemaNotFoundError as e:
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
