from fastapi import FastAPI
from .api import router as api

app = FastAPI(title="Homekey Exercise")
app.include_router(api)
