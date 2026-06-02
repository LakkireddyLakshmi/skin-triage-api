"""Manual smoke test: call the REAL Hugging Face model once and print the result.

Not part of the automated suite (those stay offline). Run by hand to confirm the
live integration works:  python smoke_test.py
"""
import asyncio
from pathlib import Path

from app import predictor

IMG = Path.home() / "SkinDiseaseClassification" / "kaggle_output_fixed" / "results" / "training_curves.png"


async def main():
    image_bytes = IMG.read_bytes()
    print(f"Calling live Space '{predictor.SPACE_ID}' (may take ~30s to wake)...")
    label, confidence = await predictor.predict(image_bytes)
    print(f"RESULT -> label={label!r}  confidence={confidence:.3f}")


if __name__ == "__main__":
    asyncio.run(main())
