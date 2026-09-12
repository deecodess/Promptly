# Promptly

Promptly is a local-first prompt compression and token-budget optimization tool. It turns long task briefs into compact LLM-ready prompts while measuring token savings, estimated input cost, and instruction retention.

## Features

- React/Vite frontend with live optimization workspace
- FastAPI backend deployed as a Vercel Python function
- Conservative, balanced, and aggressive compression modes
- Token counts, cost estimates, and preservation scoring
- Reproducible benchmark suite across 25 curated prompts
- Download and copy support for compressed prompts

## Benchmark Results

| Metric | Result |
| --- | ---: |
| Benchmark prompts | 25 |
| Average token reduction | 40.89% |
| Average preservation score | 89.27% |
| Average compression latency | ~1 ms |
| Total tokens saved | 584 |

Pricing is configured in `model_pricing.json`.

## Local Development

From the project directory:

```bash
python -m venv .venv
.venv/Scripts/activate
python -m pip install -r requirements.txt
python -m uvicorn api.index:app --reload --port 8000
```

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. On Windows PowerShell, `scripts/run_web.ps1` starts both services.

Run tests and benchmarks from the project directory:

```bash
python -m unittest discover -s tests
python benchmark.py --mode balanced --model gpt-5.4-mini
```

## Deploy to Vercel

The root `vercel.json` builds `frontend/` and serves FastAPI routes from `api/index.py` under the same domain.

```bash
vercel login
vercel
vercel --prod
```

## Project Structure

```text
.
|-- api/
|   `-- index.py
|-- benchmark.py
|-- compressor.py
|-- cost_estimator.py
|-- evaluator.py
|-- token_counter.py
|-- model_pricing.json
|-- requirements.txt
|-- vercel.json
|-- examples/
|   `-- benchmark_prompts.json
|-- frontend/
|   |-- src/
|   |-- package.json
|   `-- vite.config.js
`-- tests/
```

## Resume Bullet

Built Promptly, a React/FastAPI prompt operations tool using tokenization and extractive ranking to reduce prompt size by 40.89% across 25 benchmark prompts, with real-time token counting, API cost estimation, and 89.27% instruction preservation scoring.
