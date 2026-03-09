import marimo

__generated_with = "0.18.4"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Analyse des données DVF (Demande de valeur fonciere)
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Importation des dépendances
    """)
    return


@app.cell
def _():
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns
    import missingno as msno

    import zipfile
    import os
    import glob
    import shutil
    import time
    import requests
    import json
    from pathlib import Path

    #from config import DATA_DIR
    return Path, msno, os, pd, plt


@app.cell
def _(Path, os):
    ROUT = Path(os.path.abspath('')).parent
    DATA_DIR = ROUT / "data"
    return DATA_DIR, ROUT


@app.cell
def _(ROUT):
    print(ROUT)
    return


@app.cell
def _(DATA_DIR):
    dvf_file = DATA_DIR / 'valeursfoncieres-2025-s1.txt.zip' #gerer les chemins entre windows et linux
    return (dvf_file,)


@app.cell
def _(dvf_file, pd):
    df = pd.read_csv(dvf_file, compression='zip', sep='|', decimal=',')
    return (df,)


@app.cell
def _(df):
    df.head()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Type de données dans chaque colonnes
    """)
    return


@app.cell
def _(df):
    df[df["Prefixe de section"]=='NaN']
    return


@app.cell
def _(df):
    df.info()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Valeur de données manquante
    """)
    return


@app.cell
def _(df):
    df.isnull().sum()
    return


@app.cell
def _(df, msno):
    msno.bar(df)
    return


@app.cell
def _(df, msno):
    msno.matrix(df)
    return


@app.cell
def _(df, msno):
    msno.heatmap(df)
    return


@app.cell
def _(df, msno):
    msno.dendrogram(df)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Données unique no disposition
    """)
    return


@app.cell
def _(df):
    df['No disposition'].value_counts()
    return


@app.cell
def _(df):
    df['Date mutation'].value_counts()
    return


@app.cell
def _(df):
    df['Nature mutation'].value_counts()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Nettoyage des données
    """)
    return


@app.cell
def _(df):
    df_new = df.dropna(axis=1, how='all')
    return (df_new,)


@app.cell
def _(df_new):
    df_new
    return


@app.cell
def _(df_new, msno):
    msno.matrix(df_new)
    return


@app.cell
def _(df_new):
    df_new[df_new["Prefixe de section"]!= 'NaN']
    return


@app.cell
def _(df_new):
    df_new.fillna(0.0, inplace = True)
    return


@app.cell
def _(df_new):
    df_new[df_new["Type local"]=="Dépendance"]
    return


@app.cell
def _(df_new, msno):
    msno.matrix(df_new)
    return


@app.cell
def _(df_new, msno):
    msno.matrix(df_new[df_new["Type local"]=="Dépendance"])
    return


@app.cell
def _(df_new, msno):
    msno.matrix(df_new[df_new["Type local"]=="Appartement"])
    return


@app.cell
def _(df_new):
    df_new.duplicated().sum()
    return


@app.cell
def _(df_new):
    df_new.duplicated()
    return


@app.cell
def _(df_new):
    df_new.drop_duplicates(inplace=True)
    return


@app.cell
def _(df_new):
    df_new.duplicated().sum()
    return


@app.cell
def _(df_new):
    df_new["Valeur fonciere"].max()
    return


@app.cell
def _(df_new):
    df_new["Surface globale"] = df_new["Surface Carrez du 1er lot"] + df_new["Surface Carrez du 2eme lot"] + df_new["Surface Carrez du 3eme lot"] + df_new["Surface Carrez du 4eme lot"] + df_new["Surface Carrez du 5eme lot"]
    return


@app.cell
def _(df_new):
    df_new["Prix m2"] = df_new["Valeur fonciere"]/df_new["Surface globale"]
    return


@app.cell
def _(df_new):
    df_new[df_new["Surface globale"] > 0][["Surface globale", "Valeur fonciere", "Prix m2", "Code postal"]]
    return


@app.cell
def _(df_new):
    df_new["Prix m2"]
    return


@app.cell
def _(df_new, plt):
    df_new.boxplot(column="Valeur fonciere", vert=False)
    plt.title("Boîte à moustaches de la Valeur Foncière")
    plt.xlabel("Valeur foncière (€)")
    plt.show()
    return


@app.cell
def _(df, plt):
    plt.figure(figsize=(8, 5))
    df.boxplot(column="Valeur fonciere", vert=False)
    plt.xscale("log")  # Échelle logarithmique
    plt.title("Boîte à moustaches (échelle logarithmique) de la Valeur Foncière")
    plt.xlabel("Valeur foncière (€) [échelle log]")
    plt.show()
    return


@app.cell
def _(df_filtre, plt):
    plt.figure(figsize=(8,5))
    df_filtre.boxplot(column="Valeur fonciere", vert=False)
    plt.xscale("log")
    plt.title("Boîte à moustaches (filtrée + log) de la Valeur Foncière")
    plt.xlabel("Valeur foncière (€) [échelle log]")
    plt.show()
    return


@app.cell
def _(df_new):
    df_new[df_new.duplicated()]
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()

