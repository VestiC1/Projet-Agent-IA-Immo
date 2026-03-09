import marimo

__generated_with = "0.18.4"
app = marimo.App()


@app.cell
def _():
    from pickle import load
    import pandas as pd
    from sklearn.model_selection import train_test_split
    import shap
    import numpy as np
    import matplotlib.pyplot as plt
    return load, np, pd, plt, shap, train_test_split


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Test
    """)
    return


@app.cell
def _():
    pipe_path = "../model/20251021-15h51m49_rf.pkl"
    data_path = "../data/clean/dvf.csv"
    return data_path, pipe_path


@app.cell
def _(load):
    def load_pipeline(pipe_path):
        with open(pipe_path, "rb") as f:
            return load(f)
    return (load_pipeline,)


@app.cell
def _(pd):
    def load_df(data_path):
        return pd.read_csv(data_path, low_memory=False, nrows=10000)
    return (load_df,)


@app.cell
def _(load_pipeline, pipe_path):
    pipe = load_pipeline(pipe_path)
    return (pipe,)


@app.cell
def _(data_path, load_df):
    df = load_df(data_path)
    return (df,)


@app.cell
def _(pd):
    def generate_Xy(df:pd.DataFrame):
        y = df['Valeur fonciere']
        X = df.drop(columns=['Valeur fonciere', 'Code departement'])
        return X,y
    return (generate_Xy,)


@app.cell
def _(train_test_split):
    def generate_train_test(X, y, test_size, random_state):
        return train_test_split(X, y, test_size=test_size, random_state=random_state)
    return (generate_train_test,)


@app.cell
def _(df, generate_Xy, generate_train_test):
    X, y = generate_Xy(df)
    X_train, X_test, y_train, y_test = generate_train_test(X, y, test_size=0.3, random_state=8)
    return X, X_test, y_test


@app.cell
def _(X_test, pipe):
    # Get scaled data
    X_test_scaled = pipe.named_steps['scaler'].transform(X_test)
    return (X_test_scaled,)


@app.cell
def _(X_test_scaled, pipe, shap):
    # SHAP analysis
    explainer = shap.TreeExplainer(pipe.named_steps['rf'])
    shap_values = explainer.shap_values(X_test_scaled)
    return explainer, shap_values


@app.cell
def _(X, X_test_scaled, shap, shap_values):
    # Visualizations
    shap.summary_plot(shap_values, X_test_scaled, feature_names=X.columns)
    return


@app.cell
def _(X, X_test_scaled, shap, shap_values):
    # Feature importance plot
    shap.summary_plot(shap_values, X_test_scaled, feature_names=X.columns, plot_type="bar")
    return


@app.cell
def _(X, X_test_scaled, explainer, shap, shap_values):
    # Individual prediction explanation
    shap.initjs()
    shap.force_plot(explainer.expected_value, shap_values[0], X_test_scaled[0], 
                    feature_names=X.columns)
    return


@app.cell
def _(X, X_test_scaled, explainer, shap, shap_values):
    # Waterfall plot for single prediction
    shap.plots.waterfall(shap.Explanation(values=shap_values[0], 
                                           base_values=explainer.expected_value,
                                           data=X_test_scaled[0],
                                           feature_names=X.columns))
    return


@app.cell
def _(X_test, X_test_scaled, np, pd):
    _rs = np.random.RandomState(0)
    df_1 = pd.DataFrame(X_test_scaled)
    df_1.columns = X_test.columns
    _corr = df_1.corr()
    _corr.style.background_gradient(cmap='coolwarm')
    return


@app.cell
def _(X_test, pipe):
    y_pred_test = pipe.predict(X_test)
    return (y_pred_test,)


@app.cell
def _(plt, y_pred_test, y_test):
    plt.scatter(y_test, y_pred_test)
    plt.plot(y_test, y_test)
    plt.xlim(1e2,5e5)
    plt.ylim(1e2,5e5)
    plt.ylabel('valeur_predite')
    plt.xlabel('vraie_valeur')
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # RandomForestRegressor
    """)
    return


@app.cell
def _():
    pipe_path_rf = '../model/20251023-12h32m43_rf.pkl'
    data_path_1 = '../data/clean/dvf.csv'
    return (pipe_path_rf,)


@app.cell
def _(load_pipeline, pipe_path_rf):
    pipe_rf = load_pipeline(pipe_path_rf)
    return (pipe_rf,)


@app.cell
def _(X_test, pipe_rf):
    # Get scaled data
    X_test_scaled_rf = pipe_rf.named_steps['scaler'].transform(X_test)
    return (X_test_scaled_rf,)


@app.cell
def _(X_test_scaled_rf, pipe_rf, shap):
    # SHAP analysis
    explainer_1 = shap.TreeExplainer(pipe_rf.named_steps['rf'])
    shap_values_1 = explainer_1.shap_values(X_test_scaled_rf)
    return explainer_1, shap_values_1


@app.cell
def _(X, X_test_scaled_rf, shap, shap_values_1):
    # Visualizations
    shap.summary_plot(shap_values_1, X_test_scaled_rf, feature_names=X.columns)
    return


@app.cell
def _(X, X_test_scaled_rf, shap, shap_values_1):
    # Feature importance plot
    shap.summary_plot(shap_values_1, X_test_scaled_rf, feature_names=X.columns, plot_type='bar')
    return


@app.cell
def _(X, X_test_scaled_rf, explainer_1, shap, shap_values_1):
    # Individual prediction explanation
    shap.initjs()
    shap.force_plot(explainer_1.expected_value, shap_values_1[0], X_test_scaled_rf[0], feature_names=X.columns)
    return


@app.cell
def _(X, X_test_scaled_rf, explainer_1, shap, shap_values_1):
    # Waterfall plot for single prediction
    shap.plots.waterfall(shap.Explanation(values=shap_values_1[0], base_values=explainer_1.expected_value, data=X_test_scaled_rf[0], feature_names=X.columns))
    return


@app.cell
def _(X_test, X_test_scaled_rf, np, pd):
    _rs = np.random.RandomState(0)
    df_2 = pd.DataFrame(X_test_scaled_rf)
    df_2.columns = X_test.columns
    _corr = df_2.corr()
    _corr.style.background_gradient(cmap='coolwarm')
    return


@app.cell
def _(X_test, pipe_rf):
    y_pred_test_rf = pipe_rf.predict(X_test)
    return (y_pred_test_rf,)


@app.cell
def _(plt, y_pred_test_rf, y_test):
    plt.figure(figsize=(8, 6))
    plt.scatter(y_test, y_pred_test_rf, alpha=0.5, color='blue')
    plt.plot([min(y_pred_test_rf), max(y_pred_test_rf)], [min(y_pred_test_rf), max(y_pred_test_rf)], '--r', linewidth=2)  # Ligne idéale y=x
    plt.xlabel('Valeurs réelles (y_pred_test_rf)')
    plt.ylabel('Prédictions (y_pred_test_rf)')
    plt.title('Prédictions vs Valeurs réelles')
    plt.grid(True)
    plt.xlim(1e4, 1e6)
    plt.ylim(1e4, 1e6)
    plt.show()
    return


@app.cell
def _(plt):
    # Données
    _scores = [0.7254344288834348, 0.7238928155416253]
    _labels = ['Train', 'Test']
    _colors = ['#1f77b4', '#ff7f0e']  # Bleu et orange pour différencier
    plt.figure(figsize=(6, 4))
    # Création du graphique
    _bars = plt.barh(_labels, _scores, color=_colors, height=0.5)
    for _bar in _bars:
        _width = _bar.get_width()
    # Ajouter les valeurs sur les barres
        plt.text(_width + 0.01, _bar.get_y() + _bar.get_height() / 2, f'{_width:.3f}', va='center', ha='left')
    plt.xlabel('Score R²')
    plt.title('Comparaison des scores R² (Train vs Test)')  # Position x (juste après la barre)
    plt.xlim(0, 1)  # Position y (centré verticalement)
    plt.grid(axis='x', linestyle='--', alpha=0.7)  # Valeur du score
    plt.tight_layout()
    # Personnalisation
    # Afficher
    plt.show()  # Le R² est compris entre 0 et 1
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # XGBoost
    """)
    return


@app.cell
def _():
    pipe_path_xg = '../model/20251023-14h30m14_xg.pkl'
    data_path_2 = '../data/clean/dvf.csv'
    return (pipe_path_xg,)


@app.cell
def _(load_pipeline, pipe_path_xg):
    pipe_xg = load_pipeline(pipe_path_xg)
    return (pipe_xg,)


@app.cell
def _(X_test, pipe_xg):
    # Get scaled data
    X_test_scaled_xg = pipe_xg.named_steps['scaler'].transform(X_test)
    return (X_test_scaled_xg,)


@app.cell
def _(X_test_scaled_xg, pipe_xg, shap):
    # SHAP analysis
    explainer_2 = shap.TreeExplainer(pipe_xg.named_steps['xg'])
    shap_values_2 = explainer_2.shap_values(X_test_scaled_xg)
    return explainer_2, shap_values_2


@app.cell
def _(X, X_test_scaled_xg, shap, shap_values_2):
    # Visualizations
    shap.summary_plot(shap_values_2, X_test_scaled_xg, feature_names=X.columns)
    return


@app.cell
def _(X, X_test_scaled_xg, shap, shap_values_2):
    # Feature importance plot
    shap.summary_plot(shap_values_2, X_test_scaled_xg, feature_names=X.columns, plot_type='bar')
    return


@app.cell
def _(X, X_test_scaled_xg, explainer_2, shap, shap_values_2):
    # Individual prediction explanation
    shap.initjs()
    shap.force_plot(explainer_2.expected_value, shap_values_2[0], X_test_scaled_xg[0], feature_names=X.columns)
    return


@app.cell
def _(X, X_test_scaled_xg, explainer_2, shap, shap_values_2):
    # Waterfall plot for single prediction
    shap.plots.waterfall(shap.Explanation(values=shap_values_2[0], base_values=explainer_2.expected_value, data=X_test_scaled_xg[0], feature_names=X.columns))
    return


@app.cell
def _(X_test, X_test_scaled_xg, np, pd):
    _rs = np.random.RandomState(0)
    df_3 = pd.DataFrame(X_test_scaled_xg)
    df_3.columns = X_test.columns
    _corr = df_3.corr()
    _corr.style.background_gradient(cmap='coolwarm')
    return


@app.cell
def _(X_test, pipe_xg):
    y_pred_test_xg = pipe_xg.predict(X_test)
    return (y_pred_test_xg,)


@app.cell
def _(plt, y_pred_test_xg, y_test):
    plt.figure(figsize=(8, 6))
    plt.scatter(y_test, y_pred_test_xg, alpha=0.5, color='blue')
    plt.plot([min(y_pred_test_xg), max(y_pred_test_xg)], [min(y_pred_test_xg), max(y_pred_test_xg)], '--r', linewidth=2)  # Ligne idéale y=x
    plt.xlabel('Valeurs réelles (y_pred_test_xg)')
    plt.ylabel('Prédictions (y_pred_test_xg)')
    plt.title('Prédictions vs Valeurs réelles')
    plt.grid(True)
    plt.xlim(1e4, 1e6)
    plt.ylim(1e4, 1e6)
    plt.show()
    return


@app.cell
def _(plt):
    # Données
    _scores = [0.8490156092236925, 0.7713512490042018]
    _labels = ['Train', 'Test']
    _colors = ['#1f77b4', '#ff7f0e']  # Bleu et orange pour différencier
    plt.figure(figsize=(6, 4))
    # Création du graphique
    _bars = plt.barh(_labels, _scores, color=_colors, height=0.5)
    for _bar in _bars:
        _width = _bar.get_width()
    # Ajouter les valeurs sur les barres
        plt.text(_width + 0.01, _bar.get_y() + _bar.get_height() / 2, f'{_width:.3f}', va='center', ha='left')
    plt.xlabel('Score R²')
    plt.title('Comparaison des scores R² (Train vs Test)')  # Position x (juste après la barre)
    plt.xlim(0, 1)  # Position y (centré verticalement)
    plt.grid(axis='x', linestyle='--', alpha=0.7)  # Valeur du score
    plt.tight_layout()
    # Personnalisation
    # Afficher
    plt.show()  # Le R² est compris entre 0 et 1
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()

