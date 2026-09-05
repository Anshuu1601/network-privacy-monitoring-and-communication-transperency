"""Capture control endpoints: interface list, start/stop, demo mode."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.monitor import monitor

router = APIRouter(prefix="/api/capture", tags=["capture"])


class CaptureAction(BaseModel):
    mode: str = "auto"  # "live" | "demo"


class InterfaceSelect(BaseModel):
    interface: str


@router.get("/interfaces")
def list_interfaces():
    return monitor._ensure_capture().list_interfaces()


@router.get("/status")
def capture_status():
    return monitor.status()


@router.post("/start")
def start_capture(payload: CaptureAction | None = None):
    try:
        if payload and payload.mode == "demo":
            monitor.set_demo_mode(True)
        elif payload and payload.mode == "live":
            monitor.set_demo_mode(False)
        return monitor.start()
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=f"Packet capture permission denied: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to start capture: {exc}")


@router.post("/stop")
def stop_capture():
    return monitor.stop()


@router.post("/interface")
def select_interface(payload: InterfaceSelect):
    if not payload.interface:
        raise HTTPException(status_code=400, detail="Interface name required")
    return monitor.set_interface(payload.interface)