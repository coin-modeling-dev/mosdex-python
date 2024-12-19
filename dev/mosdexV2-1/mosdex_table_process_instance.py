from mosdex_table import MosdexTable

class MosdexTable(Base):
    # Other methods

    def process_instance(self, instance_data, engine):
        import pandas as pd
        from sqlalchemy.orm import Session

        # Create DataFrame
        col_names = self.table_schema['NAME']
        data_df = pd.DataFrame(instance_data, columns=col_names)

        # Insert into the table
        with Session(engine) as session:
            data_df.to_sql(name=self.__tablename__, con=session.connection(), if_exists="append", index=False)
            session.commit()