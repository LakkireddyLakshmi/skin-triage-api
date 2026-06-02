"""
Turns an uploaded image into a prediction by calling the deployed model.

The deep-learning model runs as a Gradio app on Hugging Face Spaces
(see settings.hf_space_url). We do NOT load the model here — we send the image
to that Space and read back its top prediction. The Space sleeps when idle, so
the first call may need to wake it; we retry a few times before giving up.
"""
import asyncio
import os
import re
import tempfile

import gradio_client.utils as _gcu

# --- Work around a gradio_client bug: boolean JSON schemas crash the API
# parser with "argument of type 'bool' is not iterable". The Space itself
# patches this server-side; we need the same guard client-side. ---
_orig_json_schema = _gcu._json_schema_to_python_type


def _safe_json_schema(schema, defs=None):
    if isinstance(schema, bool):
        return "Any"
    try:
        return _orig_json_schema(schema, defs)
    except (TypeError, KeyError):
        return "Any"


_gcu._json_schema_to_python_type = _safe_json_schema

_orig_get_type = _gcu.get_type


def _safe_get_type(schema):
    if isinstance(schema, bool):
        return "Any"
    try:
        return _orig_get_type(schema)
    except TypeError:
        return "Any"


_gcu.get_type = _safe_get_type
# --- end workaround ---

from gradio_client import Client, handle_file  # noqa: E402

# Repo id form, e.g. "sweety783/skin-disease-classifier".
SPACE_ID = "sweety783/skin-disease-classifier"

_client: Client | None = None


def _get_client() -> Client:
    """Connect to the Space once and reuse the connection."""
    global _client
    if _client is None:
        # verbose=False avoids status prints that crash on Windows consoles
        # (the library prints a "✔" the default cp1252 console can't encode).
        _client = Client(SPACE_ID, verbose=False)
    return _client


def _parse_top_prediction(predictions_html: str) -> tuple[str, float]:
    """Pull the top class name and its percentage out of the Space's HTML output."""
    classes = re.findall(r'pred-class">([^<]+)<', predictions_html)
    percents = re.findall(r">([\d.]+)%<", predictions_html)
    if not classes or not percents:
        return ("unknown", 0.0)
    label = classes[0].strip()
    confidence = float(percents[0]) / 100.0
    return (label, confidence)


def _predict_sync(image_bytes: bytes) -> tuple[str, float]:
    """Blocking call to the Space; run off the event loop via asyncio.to_thread."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name
    try:
        client = _get_client()
        # fn=predict in the Space is exposed as the "/predict" endpoint.
        result = client.predict(handle_file(tmp_path), api_name="/predict")
        predictions_html = result[0] if isinstance(result, (list, tuple)) else result
        return _parse_top_prediction(predictions_html)
    finally:
        os.unlink(tmp_path)


async def predict(image_bytes: bytes, attempts: int = 6) -> tuple[str, float]:
    """Return (predicted_label, confidence). Retries to allow the Space to wake.

    A fully-asleep Hugging Face Space can take ~60-90s to start, so we retry
    with a wait between attempts rather than failing on the first miss.
    """
    if not image_bytes:
        raise ValueError("Empty image upload.")

    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return await asyncio.to_thread(_predict_sync, image_bytes)
        except Exception as exc:  # connection refused / space waking / transient
            last_error = exc
            # Reset the cached client so the next try reconnects to a woken Space.
            global _client
            _client = None
            if attempt < attempts - 1:
                await asyncio.sleep(15)

    raise RuntimeError(
        f"The prediction service is unavailable right now: {last_error}"
    )
