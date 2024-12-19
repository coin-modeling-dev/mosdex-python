class MosdexTable(Base):
    # Other methods

    def process_query(self, query_data, engine):
        from sqlalchemy.orm import Session
        from sqlalchemy.sql import text

        for statement in query_data:
            stmt = (
                f"INSERT INTO {self.__tablename__} "
                f"({','.join(self.table_schema['NAME'])}) "
                f"SELECT {','.join(statement['SELECT'])} "
                f"FROM {','.join(statement['FROM'])}"
            )

            # Add JOIN
            if "JOIN" in statement:
                stmt += f" JOIN {' JOIN '.join(statement['JOIN'])}"

            # Add WHERE
            if "WHERE" in statement:
                stmt += f" WHERE {' '.join(statement['WHERE'])}"

            # Execute Query
            with Session(engine) as session:
                session.execute(text(stmt))
                session.commit()