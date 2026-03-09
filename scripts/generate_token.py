from config import TOKENDB
from tinydb import Query
from typing import Dict
from src.utils.csrf_token import generate_csrf_token


from src.database.jsondb_crud import get_db, insert, search

def get_token_list(db) : 
    """Function to get the authorized token list from the database."""
    Token = Query()
    tokens = search(db, Token.token.exists(), table_name='tokens')
    if len(tokens) > 0 :
        return [token['token'] for token in tokens]
    return None

def insert_token(db, token_value:str) :
    """Function to insert a new token into the database."""
    json_data : Dict = {"token" : token_value}
    insert(db=db, json_data=json_data, table_name='tokens')

def register_new_token(db) :
    """Function to generate and register a new token into the database."""
    new_token = generate_csrf_token()
    insert_token(db=db, token_value=new_token)
    return new_token

if __name__ == "__main__":
    print(f"Token database path: {TOKENDB}")
    with get_db(TOKENDB) as db:
        new_token = register_new_token(db=db)
        print(f"Generated and registered new token: {new_token}")
        