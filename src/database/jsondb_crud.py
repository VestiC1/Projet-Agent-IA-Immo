from config import TOKENDB
from tinydb import TinyDB, Query
from pathlib import Path
from typing import Dict, Union, Optional

# TODO : No update method yet

def get_db(db_path:Union[str, Path]):
    """Function to get the token database path."""
    return TinyDB(db_path)

def insert(db, json_data : Dict, table_name: Optional[str]):
    """Function to insert data into the token database.
    Params :
        db : TinyDB instance
        json_data : Dict - data to insert
        table_name : str - name of the table to insert data into
    """
    if table_name is not None :
        table = db.table(table_name)
    else :
        table = db
        
    table.insert(json_data)

def search(db, query:Query, table_name: Optional[str]):
    """Function to search data in the token database.
    Params :
        db : TinyDB instance
        query : Query - query to search
        table_name : str - name of the table to search data from
    Returns :
        List of matching documents
    """
    if table_name is not None :
        table = db.table(table_name)
    else :
        table = db
        
    return table.search(query)

def drop(db, table_name: Optional[str]=None):
    """Function to drop a table from the token database.
    Params :
        db : TinyDB instance
        table_name : str - name of the table to drop
    """
    if table_name is not None :
        db.drop_table(table_name)
    else :
        db.drop_tables()