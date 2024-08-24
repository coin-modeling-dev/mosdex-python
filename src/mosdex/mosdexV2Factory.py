import json
import pprint

from jsonschema.validators import Draft7Validator


from src.mosdex.exceptions import MosdexInvalidFileError
from src.mosdex.mosdex_database import MosdexDatabase
from src.mosdex.mosdexV2 import MosdexV2


class MosdexV2Factory:

    database: MosdexDatabase

    def __init__(self, schema_file: str, database: MosdexDatabase):
        """
        Initializes a new instance of the MosdexV2 class.
        :param schema_file: path to Mosdex schema file.
        """
        with open(schema_file) as f:
            schema_json = json.load(f)
        self.validator = Draft7Validator(schema_json)
        self.database = database

    def from_file(self, mosdex_file: str):
        """
        Create a new instance of a MosdexModel from a Mosdex file.
        :param mosdex_file: Path to Mosdex file.
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

            return MosdexV2(problem_json, self.database)

        except MosdexInvalidFileError as e:
            print(f"File {e.filename} is not a valid Mosdex file.")
            pp = pprint.PrettyPrinter(indent=4)
            for error in sorted(e.invalid_items, key=str):
                print()
                pp.pprint(error.message)

 