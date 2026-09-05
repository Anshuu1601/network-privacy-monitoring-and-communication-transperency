"""FastAPI application entrypoint."""
import asyncio
import logging
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import alerts, capture, devices, dns, privacy, reports, services, settings, traffic, websites
from app.config import BASE_DIR, settings as app_settings
from app.database.database import init_db
from app.monitor import monitor
from app.websocket.manager import manager

logger = logging.getLogger("privacy")

FRONTEND_DIST = BASE_DIR / "frontend" / "dist"


def setup_logging():
    root = logging.getLogger()
    root.setLevel(getattr(logging, app_settings.LOG_LEVEL.upper(), logging.INFO))
    formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")

    app_settings.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        app_settings.LOG_FILE, maxBytes=2_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    init_db()
    # Reference the running event loop so background capture threads can
    # schedule WebSocket broadcasts onto it (the root cause of missing
    # real-time updates: broadcasts were scheduled on a never-running loop).
    manager.set_loop(asyncio.get_running_loop())
    logger.info("Starting %s", app_settings.APP_NAME)
    logger.info("Database: %s", app_settings.DATABASE_URL)
    yield
    if monitor.capture is not None and monitor.capture.is_running:
        monitor.stop()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=app_settings.APP_NAME,
    version="1.0.0",
    description=(
        "Real-time network metadata monitoring focused on privacy visibility, "
        "encryption status, data usage, services and connection history. "
        "Does not decrypt or store private communication content."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "application": app_settings.APP_NAME,
        "database": "connected",
        "monitoring": monitor.status(),
        "version": "1.0.0",
    }


@app.get("/api/interfaces")
def interfaces():
    return monitor._ensure_capture().list_interfaces()


@app.websocket("/ws/traffic")
async def ws_traffic(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        try:
            await websocket.send_json(monitor.live_payload())
        except Exception:
            pass
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as exc:
        logger.warning("WebSocket error: %s", exc)
        await manager.disconnect(websocket)


app.include_router(traffic.router)
app.include_router(devices.router)
app.include_router(privacy.router)
app.include_router(services.router)
app.include_router(websites.router)
app.include_router(dns.router)
app.include_router(alerts.router)
app.include_router(reports.router)
app.include_router(capture.router)
app.include_router(settings.router)


def _serve_frontend():
    """Serve the built React dashboard from the backend so the whole app is
    available at http://127.0.0.1:8000 without a separate Vite process."""
    index = FRONTEND_DIST / "index.html"
    assets = FRONTEND_DIST / "assets"
    if not index.exists():
        logger.warning(
            "Frontend build not found at %s. Run `npm run build` in frontend/ "
            "or use the Vite dev server on :5173.", FRONTEND_DIST
        )
        return

    if assets.exists():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        if full_path.startswith(("api/", "ws/")):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        if full_path and (FRONTEND_DIST / full_path).is_file():
            return FileResponse(FRONTEND_DIST / full_path)
        return FileResponse(index)


_serve_frontend()