from config import dvf_clean, MODEL_DIR
from src.utils.load_models import load_pickle
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType, Int64TensorType, StringTensorType, DoubleTensorType
from sklearn.model_selection import train_test_split
import onnxruntime as rt


import pandas as pd

def load_df(data_path):
    return pd.read_csv(data_path, low_memory=False)

def generate_Xy(df: pd.DataFrame):
    y = df['Valeur fonciere']
    X = df.drop(columns=['Valeur fonciere', 'Code departement'])
    return X, y

def infer_onnx_types(df: pd.DataFrame) -> list:
    """Automatically infer ONNX types from DataFrame dtypes"""
    
    initial_types = []
    
    for col in df.columns:
        dtype = df[col].dtype
        
        if dtype in ['float32', 'float16']:
            onnx_type = FloatTensorType([None, 1])
        elif dtype == 'float64':
            onnx_type = DoubleTensorType([None, 1])
        elif dtype in ['int32', 'int64', 'int16', 'int8']:
            onnx_type = Int64TensorType([None, 1])
        elif dtype == 'object' or dtype.name == 'category':
            onnx_type = StringTensorType([None, 1])
        else:
            # Default to float for unknown types
            onnx_type = FloatTensorType([None, 1])
        
        initial_types.append((col, onnx_type))
    
    return initial_types

def generate_train_test(X, y, test_size, random_state):
    return train_test_split(X, y, test_size=test_size, random_state=random_state)

pipeline = load_pickle("20251022-16h17m18_rf.pkl")
df = load_df(dvf_clean)
X, y = generate_Xy(df)

X_train, X_test, y_train, y_test = generate_train_test(X, y, test_size=0.3, random_state=8)

# Define input shape (number of raw features)
initial_type = infer_onnx_types(X_train)

# Convert - this includes ALL preprocessing steps!
onnx_model = convert_sklearn(
    pipeline,  # Your full pipeline
    initial_types = initial_type,
    final_types=[('output', DoubleTensorType([None, 1]))],
    target_opset = 17
)

model_path = MODEL_DIR / 'model.onnx'

# Save ONNX
with open(MODEL_DIR / 'model.onnx', 'wb') as f:
    f.write(onnx_model.SerializeToString())

print("✅ Full pipeline converted to ONNX!")

session = rt.InferenceSession(str(model_path))
input_names = session.get_inputs()
import numpy as np
j = 3123
xx = {innput.name: np.array([[X_test.iloc[j, i]]]) for i, innput in enumerate(input_names)}


xx = {
    'Code_postal' :  np.array([[10200.0]]),
    'Code_commune' :  np.array([[33.0]]).astype(np.int64),
    'Surface_habitable' : np.array([[0.0]]),
    'Nombre_pieces_principales' : np.array([[0.0]]),
    'Surface_reelle_bati' : np.array([[0.0]]),
    'Surface_terrain' : np.array([[217.0]])
}

#print(X_test.iloc[j, :])
prediction = session.run(None, xx)[0][0,0]
y_pred = pipeline.predict(X_test.iloc[[j]])[0]
print(prediction)

print(y_pred)