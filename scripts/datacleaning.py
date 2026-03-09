from config import DVF, dvf_clean
import pandas as pd


def load_df(data_path):
    return pd.read_csv(data_path, sep='|', decimal=",", compression="zip", low_memory=False)

def save_df(df, df_path):
    df.to_csv(df_path, index=False)

def clean_df(df):
    # Sélection des colonnes pour calculer [Surface habitable]
    df_new = df[['Date mutation', 'Nature mutation', 'Valeur fonciere', 'Code postal', 'Code departement', 'Code commune', 'Surface Carrez du 1er lot', 'Surface Carrez du 2eme lot', 'Surface Carrez du 3eme lot', 'Surface Carrez du 4eme lot', 'Surface Carrez du 5eme lot', 'Nombre pieces principales', 'Surface reelle bati', 'Surface terrain']]
    # Suppression des doublons
    df_new = df_new.drop_duplicates()
    # Remplacement des NaN par 0.00 dans les colonnes avec des valeurs numerique pour le calcul de [Surface habitable]
    df_new = df_new.fillna(.0)
    # Calcul de [Surface habitable]
    df_new["Surface habitable"] = df_new["Surface Carrez du 1er lot"] + df_new["Surface Carrez du 2eme lot"] + df_new["Surface Carrez du 3eme lot"] + df_new["Surface Carrez du 4eme lot"] + df_new["Surface Carrez du 5eme lot"]
    # Sélection des colonnes
    df_new = df_new[['Valeur fonciere', 'Code postal', 'Code departement', 'Code commune', 'Surface habitable', 'Nombre pieces principales', 'Surface reelle bati', 'Surface terrain']]
    return df_new

def main():
    df=load_df(DVF)
    df=clean_df(df)

    save_df(df, dvf_clean)

if __name__ == "__main__":
    main()