"""Utilitaires HuggingFace (HTTP, inference) — point d'entree unique pour tous les skills."""
import logging
import os
import requests

HF_KEY = os.getenv("HF_API_KEY", "")
HF_ROUTER = "https://router.huggingface.co"


def hf_call(endpoint: str, payload: dict, timeout: int = 20) -> dict:
    if not HF_KEY:
        return {"error": "HF_API_KEY absent"}
    try:
        url = f"{HF_ROUTER}/{endpoint}"
        r = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {HF_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=timeout,
        )
        if r.status_code == 200:
            return r.json()
        return {"error": f"HTTP {r.status_code}", "detail": r.text[:120]}
    except Exception as e:
        return {"error": str(e)}


def hf_inference(model: str, payload: dict, timeout: int = 20) -> dict:
    return hf_call(f"hf-inference/models/{model}", payload, timeout)


def hf_status() -> dict:
    status = {"available": bool(HF_KEY)}
    if not HF_KEY:
        return status
    try:
        r = requests.get(
            f"{HF_ROUTER}/v1/models",
            headers={"Authorization": f"Bearer {HF_KEY}"},
            timeout=10,
        )
        status["models_available"] = (
            len(r.json().get("data", [])) if r.status_code == 200 else 0
        )
    except Exception:
        status["models_available"] = "unreachable"
    return status
