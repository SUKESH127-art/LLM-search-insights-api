# database.py

import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

# Define a naming convention for all database constraints.
# This makes your database schema clean and predictable.
POSTGRES_INDEXES_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

# TODO: change back echo=true in prod
engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Create a MetaData object with the naming convention
metadata_obj = MetaData(naming_convention=POSTGRES_INDEXES_NAMING_CONVENTION)

# Create a new Base class with AsyncAttrs support
# This is the modern SQLAlchemy 2.0 approach
class Base(AsyncAttrs, DeclarativeBase):
    metadata = metadata_obj