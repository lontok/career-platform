from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import Settings
from app.db.session import create_session_factory
from app.routers import router as pages_router

BASE_DIR = Path(__file__).resolve().parent


def create_app() -> FastAPI:
    app = FastAPI()
    app.state.settings = Settings()
    database_engine, session_factory = create_session_factory(
        app.state.settings.database_url
    )
    app.state.database_engine = database_engine
    app.state.session_factory = session_factory
    app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
    app.include_router(pages_router)

    @app.get("/health")
    def health() -> JSONResponse:
        return JSONResponse({"status": "ok"})

    return app


app = create_app()
