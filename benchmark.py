"""Run the Promptly benchmark suite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evaluator import benchmark, load_prompts


PROMPTS_FILE = Path("examples") / "benchmark_prompts.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark Promptly compression metrics.")
    parser.add_argument("--mode", choices=["conservative", "balanced", "aggressive"], default="balanced")
    parser.add_argument("--model", default="gpt-5.4-mini")
    parser.add_argument("--input", type=Path, default=PROMPTS_FILE)
    parser.add_argument("--json", action="store_true", help="Print full JSON output.")
    args = parser.parse_args()

    prompts = load_prompts(args.input)
    report = benchmark(prompts, mode=args.mode, model_name=args.model)

    if args.json:
        print(json.dumps(report, indent=2))
        return

    summary = report["summary"]
    print("Promptly benchmark")
    print(f"Mode: {args.mode}")
    print(f"Model: {args.model}")
    print(f"Prompts: {summary['prompt_count']}")
    print(f"Average token reduction: {summary['avg_reduction_pct']}%")
    print(f"Average preservation score: {summary['avg_preservation_score']}%")
    print(f"Average latency: {summary['avg_latency_ms']} ms")
    print(f"Total tokens saved: {summary['total_tokens_saved']}")
    print(f"Estimated input cost saved: ${summary['total_estimated_cost_saved']:.8f}")


if __name__ == "__main__":
    main()
