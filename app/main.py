from fastapi import FastAPI

from . import models
from .database import engine
from .routers import auth, drivers, favorites

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="F1 Logbook API")

app.include_router(drivers.router)
app.include_router(auth.router)
app.include_router(favorites.router)


@app.get("/")
def root():
    return {"message": "F1 Logbook API is running"}


# uvicorn app.main:app --reload

# TODO! Crear endpoints para todos los favoritos (circuitos y carreras)

# TODO! Crear tablas con resultado de carrera

# TODO! Crear tablas con historial de piloto

# TODO! Crear sync para sincronizar datos con la API Jolpica

# Duda: ¿Hay una manera mejor de crear admin que no sea directamente desde postgres?
