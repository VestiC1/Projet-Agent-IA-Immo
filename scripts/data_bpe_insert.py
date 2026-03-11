from config import BPE_INSEE, BPE_INSEE_DB
import duckdb
import pandas as pd
from src.agent.tools.commune_info import get_commune_info


con = duckdb.connect(BPE_INSEE_DB)

def create_schema(con):
    con.sql("CREATE OR REPLACE TABLE count_equipements (code_insee VARCHAR(8) PRIMARY KEY, nom_commune VARCHAR(128))")

def add_column(con, table, col, type_):
    con.sql(f"ALTER TABLE {table} ADD COLUMN {col} {type_} DEFAULT 0")

def add_line(con, table, col, df):
    con.sql(f"""INSERT INTO {table} (code_insee, nom_commune, {col})
            SELECT "0","1",count_bpe FROM df
            ON CONFLICT (code_insee) DO UPDATE SET
                {col} = excluded.{col}
            """)

def compute_sum(df: pd.DataFrame):
    return df.iloc[:,2:].sum(axis=1)

def clean(df : pd.DataFrame) : 

    df = df.dropna(subset=[0, 1])
    df = df.fillna(0.0)

    return df

def main():
    """
    create_schema(con)
    for file in BPE_INSEE.glob("*"):

        col = file.stem.lower()
        add_column(con=con, table="count_equipements", col=col, type_="int")
        
        print ("lecture ", file.stem)
        df=pd.read_excel(file, sheet_name="COM", skiprows=10, engine="openpyxl", header=None)
        df = clean(df)

        print("count equipements")
        df['count_bpe']  = compute_sum(df)
        print("count insert")
        add_line(con=con, table="count_equipements", col=col, df=df)
    """
    df = con.sql("SELECT * FROM count_equipements").df()
    print(df)
    print(get_commune_info(con, "37261"))

if __name__ == "__main__":
    main()