"""Streamlit UI for Promptly."""

from __future__ import annotations

from compressor import MODE_RATIOS, compress_prompt
from cost_estimator import available_models, estimate_savings, format_usd, load_pricing
from evaluator import preservation_score


SAMPLE_PROMPT = """You are helping a product team summarize customer feedback.
Please produce a concise brief for executives. Include the top complaints, feature requests,
risks, and recommended next steps. Do not invent details. Output the result as markdown with
sections for Summary, Evidence, Risks, and Actions. The brief should be easy to scan."""


def main() -> None:
    try:
        import streamlit as st
    except ImportError as exc:
        raise SystemExit(
            "Streamlit is not installed. Run `python -m pip install -r requirements.txt` "
            "then start the app with `streamlit run app.py`."
        ) from exc

    st.set_page_config(page_title="Promptly", page_icon="Promptly", layout="wide")

    st.title("Promptly")
    st.caption("Prompt compression, token savings, and cost estimation for LLM workflows.")

    models = available_models()
    pricing = load_pricing()

    with st.sidebar:
        st.header("Compression")
        mode = st.radio("Mode", list(MODE_RATIOS.keys()), index=1)
        model_name = st.selectbox("Model pricing", models, index=min(2, len(models) - 1))
        st.caption(f"Input price: ${pricing[model_name]['input_per_million']} per 1M tokens")

    prompt = st.text_area(
        "Prompt",
        value=SAMPLE_PROMPT,
        height=300,
        placeholder="Paste a long prompt, requirements document, or task brief...",
    )

    result = compress_prompt(prompt, mode)
    costs = estimate_savings(result.original_tokens, result.compressed_tokens, model_name)
    quality = preservation_score(result.original, result.compressed)

    metric_cols = st.columns(5)
    metric_cols[0].metric("Original tokens", f"{result.original_tokens:,}")
    metric_cols[1].metric("Compressed tokens", f"{result.compressed_tokens:,}")
    metric_cols[2].metric("Tokens saved", f"{result.saved_tokens:,}")
    metric_cols[3].metric("Reduction", f"{result.reduction_pct:.1f}%")
    metric_cols[4].metric("Preservation", f"{quality:.1f}%")

    cost_cols = st.columns(3)
    cost_cols[0].metric("Cost before", format_usd(costs["cost_before"]))
    cost_cols[1].metric("Cost after", format_usd(costs["cost_after"]))
    cost_cols[2].metric("Estimated saved", format_usd(costs["cost_saved"]))

    original_col, compressed_col = st.columns(2)
    with original_col:
        st.subheader("Original")
        st.text_area("Original prompt", value=result.original, height=360, label_visibility="collapsed")
    with compressed_col:
        st.subheader("Compressed")
        st.text_area("Compressed prompt", value=result.compressed, height=360, label_visibility="collapsed")
        st.download_button(
            "Download compressed prompt",
            result.compressed,
            file_name="compressed_prompt.txt",
            mime="text/plain",
            disabled=not bool(result.compressed),
        )

    with st.expander("How metrics are calculated"):
        st.write(
            "Token counts use tiktoken when installed, with a deterministic fallback for local testing. "
            "Cost savings estimate input-token cost from `model_pricing.json`. Preservation score checks "
            "whether important instructions, constraints, quoted terms, and output-format markers survive compression."
        )


if __name__ == "__main__":
    main()
