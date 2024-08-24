from records import Database

class MosdexDatabase(Database):

    def __init__(self, file_or_url: str):
        super().__init__(file_or_url)

    def initialize_mosdex_table(self):
        """
        Initializes mosdex table in database.
        :return:
        """
        self.query('DROP TABLE IF EXISTS mosdex')
        self.query('CREATE TABLE mosdex ( module_name text, item_name text, '
                   'class_name text, type_name text, table_name text PRIMARY KEY) ')


    def initialize_database(self, do_print=False):

        # Create modules table

        # Create the singletons table
        self.query('DROP TABLE IF EXISTS singletons_table')
        self.query('CREATE TABLE singletons_table ('
                 'module_name text, item_name text, class_name text, singleton_name text, '
                 's_value numeric, s_recipe text)')

        # Create the metadata table
        self.query('DROP TABLE IF EXISTS metadata_table')
        self.query('CREATE TABLE metadata_table ('
                 'module_name text, item_name text, class_name text, '
                 'name text, type text, usage text, key_type text, source text )')

