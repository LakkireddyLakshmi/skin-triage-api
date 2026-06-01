"""
Turns an uploaded image into a prediction.

Step 3 (current): a placeholder that returns a fixed, clearly-marked result so
the rest of the app (saving + history) can be built and tested without the
model. Step 4 replaces the body of `predict` with a real call to the deployed
Hugging Face Space — nothing else in the app needs to change.
"""


async def predict(image_bytes: bytes) -> tuple[str, float]:
    """Return (predicted_label, confidence) for an image.

    Placeholder until Step 4 wires in the Hugging Face model.
    """
    if not image_bytes:
        raise ValueError("Empty image upload.")
    return ("pending_model", 0.0)
