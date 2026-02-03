from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.errors import register_exception_handlers
from app.api.upload import router as upload_router
from app.api.extract import router as extract_router
from app.api.chunks import router as chunks_router
from app.api.metrics import router as metrics_router
from app.api.variance import router as variance_router
from app.api.ask import router as ask_router






def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(title=settings.app_name)
    register_exception_handlers(app)

    app.include_router(upload_router)
    app.include_router(extract_router)
    app.include_router(chunks_router)
    app.include_router(metrics_router)
    app.include_router(variance_router)
    app.include_router(ask_router)







    @app.get("/health")
    def health():
        return {"status": "ok", "app": settings.app_name, "env": settings.env}

    return app



app = create_app()
