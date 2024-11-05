import pandas as pd
from sqlalchemy import (create_engine, select,
                        MetaData,
                        Table,
                        PrimaryKeyConstraint, Column, String, Integer)
from sqlalchemy.orm import Session

# Create sqlite engine
engine1 = create_engine('sqlite:///test1.db')

# Create dataframe and set the index name to 'id'
df = pd.DataFrame({'name': ['User 1', 'User 2', 'User 3']})

# Method 1: load df into 'users1' table, reflect table into MetaData(), append PrimaryKeyConstraint

# load df
with Session(bind=engine1) as session:
    df.to_sql('users1', con=session.connection(), index=True, if_exists='replace')
    session.commit()

# Initialize metadata and reflect the sqlite metadata
metadata1 = MetaData()
metadata1.reflect(bind=engine1)

# Get the 'users1' table from the MetaData object
users1 = Table('users1', metadata1, autoload_with=engine1, must_exist=True)
print(users1.columns)

# Check the content of the table
print(f"Content of {users1} table")
with Session(bind=engine1) as session:
    stmt = users1.select()
    for row in session.execute(stmt):
        print(row)

# Add the 'name' column to PrimaryKeyConstraint
name_col = users1.columns['name']
users1.constraints.add(PrimaryKeyConstraint(name_col))
print(users1.primary_key)

# Method 2: create name column, add to table, then append dataframe
engine2 = create_engine('sqlite:///test17.db')

from sqlalchemy.orm import declarative_base

Base = declarative_base()

User = type('User', (Base,), {
    '__tablename__': 'users2',
    'index': Column(Integer, autoincrement=True),
    'name': Column(String, nullable=False, primary_key=True),
    }
)

metadata2 = Base.metadata
metadata2.create_all(engine2)

# load dataframe with to_sql() and check the content
with Session(bind=engine2) as session:
    df.to_sql('users2', con=session.connection(), if_exists='append')
    session.commit()

users2 = Table('users2', metadata2, autoload_with=engine2)
print("\nContent of users2 table")
with Session(bind=engine2) as session:
    stmt = users2.select()
    for row in session.execute(stmt):
        print(row)

print(users2.primary_key)
