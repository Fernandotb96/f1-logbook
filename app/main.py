from fastapi import FastAPI

from . import models
from .database import engine
from .routers import (
    auth,
    circuits,
    drivers,
    favorite_circuits,
    favorite_drivers,
    favorite_races,
    race_results,
    races,
)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="F1 Logbook API")

app.include_router(drivers.router)
app.include_router(circuits.router)
app.include_router(auth.router)
app.include_router(favorite_drivers.router)
app.include_router(favorite_circuits.router)
app.include_router(races.router)
app.include_router(favorite_races.router)
app.include_router(race_results.router)


@app.get("/")
def root():
    return {"message": "F1 Logbook API is running"}


# uvicorn app.main:app --reload

# TODO! Crear tablas con historial de piloto

# TODO! Crear sync para sincronizar datos con la API Jolpica

# TODO! Crear endpoints /creat-admin para modificar el atributo de un usuario is_admin
