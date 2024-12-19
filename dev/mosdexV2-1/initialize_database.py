def initialize_database(engine_url: str = "sqlite:///:memory:"):
    from sqlalchemy import create_engine

    engine = create_engine(engine_url)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at {engine_url}")
    return engine