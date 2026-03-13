
from config import MODEL


from src.inference.model import get_model, get_estimation

model = get_model(MODEL)

def estimate_price(address, type_local, surface_habitable, surface_terrain, nombre_pieces) :
    return get_estimation(
        model,
        address,
        type_local,
        surface_habitable,
        surface_terrain,
        nombre_pieces
    )

