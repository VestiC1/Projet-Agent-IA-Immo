import marimo

__generated_with = "0.18.4"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _():
    import pandas as pd
    import zipfile
    import missingno as msno
    return msno, pd


@app.cell
def _(pd):
    # Chemin vers ton fichier zip
    zip_path = '../data/valeursfoncieres-2025-s1.txt.zip'

    df = pd.read_csv(zip_path, sep='|', decimal=",", compression="zip", low_memory=False)

    df.head()
    return (df,)


@app.cell
def _(df):
    df.columns   # Noms des colonnes
    return


@app.cell
def _(df):
    df.info()
    return


@app.cell
def _(df):
    df.dtypes    # Types de données (int, float, object, etc.)
    return


@app.cell
def _(df):
    df.shape     # (nombre de lignes, nombre de colonnes)
    return


@app.cell
def _(df):
    df.isnull().sum()     # (Compter les valeurs manquantes)
    return


@app.cell
def _(df):
    df.describe()     # Statistiques descriptives (pour les colonnes numériques)
    return


@app.cell
def _(df):
    df.nunique()     # Nombre de valeurs uniques par colonne
    return


@app.cell
def _(df):
    df['No disposition'].unique()     # Liste des valeurs uniques pour une colonne
    return


@app.cell
def _(df):
    df.duplicated().value_counts()  # Nombre de lignes en double
    return


@app.cell
def _(df):
    df.boxplot(column='Valeur fonciere')     # Boxplots pour repérer les outliers
    return


@app.cell
def _(df, msno):
    # '%matplotlib inline' command supported automatically in marimo
    msno.matrix(df)
    return


@app.cell
def _(df):
    df['No Volume'].notnull()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Ajout de la colonne [surface habitable]
    """)
    return


@app.cell
def _(df):
    df_new = df[['Date mutation', 'Nature mutation', 'Valeur fonciere', 'Code postal', 'Code departement', 'Code commune', 'Surface Carrez du 1er lot', 'Surface Carrez du 2eme lot', 'Surface Carrez du 3eme lot', 'Surface Carrez du 4eme lot', 'Surface Carrez du 5eme lot', 'Nombre pieces principales', 'Surface reelle bati', 'Surface terrain']]
    df_new
    return (df_new,)


@app.cell
def _(df_new):
    # Suppression des doublons
    df_new_1 = df_new.drop_duplicates()
    # Remplacement des NaN par 0.00 dans les colonnes avec des valeurs numerique pour le calcul de [Surface habitable]
    df_new_1 = df_new_1.fillna(0.0)
    return (df_new_1,)


@app.cell
def _(df_new_1):
    df_new_1.loc[:, 'Surface habitable'] = df_new_1['Surface Carrez du 1er lot'] + df_new_1['Surface Carrez du 2eme lot'] + df_new_1['Surface Carrez du 3eme lot'] + df_new_1['Surface Carrez du 4eme lot'] + df_new_1['Surface Carrez du 5eme lot']
    df_new_1
    return


@app.cell
def _(df_new_1):
    df_new_2 = df_new_1[['Valeur fonciere', 'Code postal', 'Code departement', 'Code commune', 'Surface habitable', 'Nombre pieces principales', 'Surface reelle bati', 'Surface terrain']]
    df_new_2
    return (df_new_2,)


@app.cell
def _(df_new_2):
    df_new_2.dtypes
    return


if __name__ == "__main__":
    app.run()
