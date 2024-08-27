import json
import pprint
from pathlib import Path

from jsonschema.validators import Draft7Validator
from sqlalchemy.orm import Session

from src.mosdex.exceptions import MosdexInvalidFileError
from src.mosdex.mosdexV2 import MosdexV2
from src.mosdex.mosdex_db import MosdexDB
from src.mosdex.mosdex_db import MosdexFile


class MosdexV2Factory:
    schema_file: Path
    db_endpoint: str
    mosdex_db: MosdexDB


    def __init__(self, schema_file: Path, db_endpoint: str, echo: bool=False, drop_all: bool=False):
        """
        Constructor for MosdexV2Factory.
        Loads the MosdexV2 schema from schema_file and initializes the validator.
        Creates a database engine from the db_endpoint.
        Initializes the database metadata and all tables declared in MosdexBase, if required.

        :param schema_file: path to Mosdex schema file.
        :param db_endpoint: database endpoint.
        :param echo: whether database engine should echo the sent/received messages to stdout.
        :param drop_all: whether to drop all tables.
        """
        self.schema_file = schema_file
        self.db_endpoint = db_endpoint

        # Open schema file and generate validator
        with open(schema_file) as f:
            schema_json = json.load(f)
        self.validator = Draft7Validator(schema_json)

        self.mosdex_db = MosdexDB(db_endpoint, echo=echo, drop_all=drop_all)

    def from_file(self, mosdex_file: Path, tag: str = "no_tag"):
        """
        Create a new instance of a MosdexModel from a Mosdex file.

        :param mosdex_file: Path to Mosdex file.
        :param tag: Tag for this instantiation of the Mosdex file.
        :return: MosdexModel: MosdexModel instance.
        """

        problem_json = {}
        if mosdex_file is not None:
            with open(mosdex_file, 'r') as f:
                problem_json = json.load(f)

        try:
            if not self.validator.is_valid(problem_json):
                raise MosdexInvalidFileError('Invalid Mosdex file',
                                         filename=mosdex_file,
                                         invalid_items=self.validator.iter_errors(problem_json))



        except MosdexInvalidFileError as e:
            print(f"File {e.filename} is not a valid Mosdex file.")
            pp = pprint.PrettyPrinter(indent=4)
            for error in sorted(e.invalid_items, key=str):
                print()
                pp.pprint(error.message)

        with Session(self.mosdex_db.engine) as session, session.begin():
            mosdex_file = MosdexFile(syntax=self.schema_file.name,
                                     file=mosdex_file.name,
                                     tag=tag )
            session.add(mosdex_file)
            session.flush()
            file_id = mosdex_file.id


        return MosdexV2(problem_json, file_id=file_id, mosdex_db=self.mosdex_db)