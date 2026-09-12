"""FastAPI serverless entrypoint for the Promptly web frontend."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from compressor import MODE_RATIOS, compress_prompt
from cost_estimator import available_models, estimate_savings, load_pricing
from evaluator import preservation_score


class CompressRequest(BaseModel):
    prompt: str = Field(default="", max_length=100_000)
    mode: str = "balanced"
    model: str = "gpt-5.4-mini"


app = FastAPI(title="Promptly API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/config")
def config() -> dict[str, object]:
    pricing = load_pricing()
    return {"modes": list(MODE_RATIOS), "models": available_models(), "pricing": pricing}


@app.post("/api/compress")
def compress(request: CompressRequest) -> dict[str, object]:
    if request.mode not in MODE_RATIOS:
        raise HTTPException(status_code=400, detail="Unsupported compression mode")
    if request.model not in load_pricing():
        raise HTTPException(status_code=400, detail="Unknown model")

    result = compress_prompt(request.prompt, request.mode)
    costs = estimate_savings(result.original_tokens, result.compressed_tokens, request.model)
    return {
        "original": result.original,
        "compressed": result.compressed,
        "mode": result.mode,
        "original_tokens": result.original_tokens,
        "compressed_tokens": result.compressed_tokens,
        "saved_tokens": result.saved_tokens,
        "reduction_pct": result.reduction_pct,
        "preservation_score": preservation_score(result.original, result.compressed),
        **costs,
    }
