from fastapi import FastAPI

from . import models
from .database import engine
from .routers import drivers

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="F1 Logbook API")

app.include_router(drivers.router)


@app.get("/")
def root():
    return {"message": "F1 Logbook API is running"}


# uvicorn app.main:app --reload
