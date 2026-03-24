from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, text
import os
from loguru import logger

def initialize_database(db_url: str = os.getenv("DB_URL", "sqlite:///./test.db")):
    """
    Utility: Database Initialization & Migrations.
    - Seeding test data for MVP (Step 1).
    - Separation of Concerns: This is NOT the executor module's responsibility.
    """
    logger.info(f"Utils: Initializing database at {db_url}")
    engine = create_engine(db_url)
    metadata = MetaData()
    
    # 1. Define Model (MVP)
    users = Table('Users', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String),
        Column('email', String),
        Column('role', String),
        Column('created_at', String))
        
    products = Table('Products', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String),
        Column('price', Float),
        Column('stock', Integer),
        Column('category_id', Integer))
        
    categories = Table('Categories', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String))
        
    # 2. Schema Migration
    metadata.create_all(engine)
    
    # 3. Seed Mock Data
    with engine.connect() as connection:
        if connection.execute(text("SELECT count(*) FROM Users")).scalar() == 0:
            connection.execute(text("INSERT INTO Users (name, email, role) VALUES ('Admin', 'admin@example.com', 'Admin')"))
            connection.execute(text("INSERT INTO Products (name, price, stock) VALUES ('Laptop', 1200, 10)"))
            connection.execute(text("INSERT INTO Categories (name) VALUES ('Electronics')"))
            connection.commit()
            logger.info("Utils: Seeding completed.")
        else:
            logger.info("Utils: Skipping seed (Items detected).")

if __name__ == "__main__":
    initialize_database()
