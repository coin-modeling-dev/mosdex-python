from records import Database

class MosdexDatabase(Database):

    def __init__(self, file_or_url: str):
        super().__init__(file_or_url)