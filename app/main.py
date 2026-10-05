from fastapi import FastAPI

from . import models
from .database import engine
from .routers import auth, sync
from .routers.favorites import (
    favorite_circuits,
    favorite_drivers,
    favorite_races,
)
from .routers.resources import (
    circuits,
    constructors,
    driver_season_history,
    drivers,
    race_results,
    races,
    seasons,
    sprint_results,
)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="F1 Logbook API")

app.include_router(drivers.router)
app.include_router(circuits.router)
app.include_router(constructors.router)
app.include_router(seasons.router)
app.include_router(auth.router)
app.include_router(favorite_drivers.router)
app.include_router(favorite_circuits.router)
app.include_router(races.router)
app.include_router(favorite_races.router)
app.include_router(race_results.router)
app.include_router(sprint_results.router)
app.include_router(driver_season_history.router)
app.include_router(sync.router)


@app.get("/")
def root():
    return {"message": "F1 Logbook API is running"}


# uvicorn app.main:app --reload

# TODO! Crear endpoints /creat-admin para modificar el atributo de un usuario is_admin, contraseñas u otros
# TODO! Deployment
# TODO! Front-end? A lo mejor con la IA
