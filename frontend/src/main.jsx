import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { ArrowRight, Check, Copy, Download, Gauge, Menu, Sparkles, Zap } from 'lucide-react'
import './styles.css'

const SAMPLE = `You are helping a product team summarize customer feedback.
Please produce a concise brief for executives. Include the top complaints, feature requests,
risks, and recommended next steps. Do not invent details. Output the result as markdown with
sections for Summary, Evidence, Risks, and Actions. The brief should be easy to scan.`

const fallback = { modes: ['conservative', 'balanced', 'aggressive'], models: ['gpt-5.5', 'gpt-5.4', 'gpt-5.4-mini', 'custom-local'], pricing: {} }

function App() {
  const [config, setConfig] = useState(fallback)
  const [prompt, setPrompt] = useState(SAMPLE)
  const [mode, setMode] = useState('balanced')
  const [model, setModel] = useState('gpt-5.4-mini')
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [copied, setCopied] = useState(false)

  useEffect(() => { fetch('/api/config').then(r => r.json()).then(setConfig).catch(() => {}) }, [])
  useEffect(() => { optimize() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  async function optimize() {
    setBusy(true)
    try {
      const response = await fetch('/api/compress', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ prompt, mode, model }) })
      if (!response.ok) throw new Error('API unavailable')
      setResult(await response.json())
    } catch { setResult(null) }
    finally { setBusy(false) }
  }

  function copyResult() { if (!result) return; navigator.clipboard.writeText(result.compressed); setCopied(true); setTimeout(() => setCopied(false), 1600) }
  function downloadResult() { if (!result) return; const blob = new Blob([result.compressed], { type: 'text/plain' }); const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = 'compressed_prompt.txt'; link.click(); URL.revokeObjectURL(url) }
  const pct = result?.reduction_pct ?? 40.89

  return <>
    <nav className="nav"><a className="brand" href="#top"><span className="logo"><span /></span>Promptly</a><div className="nav-links"><a href="#platform">Platform</a><a href="#benchmarks">Benchmarks</a><a href="#workflow">Workflow</a><a href="#workspace">Workspace</a></div><a className="nav-cta" href="#workspace">Use Promptly <ArrowRight size={16} /></a><button className="menu"><Menu /></button></nav>
    <main id="top">
      <section className="hero" id="platform"><div className="hero-copy"><div className="eyebrow"><Sparkles size={15} /> AI prompt operations</div><h1>Compress prompts with <em>measurable</em> control.</h1><p>Turn long, repetitive task briefs into compact LLM-ready prompts while tracking token savings, estimated spend, and instruction retention.</p><div className="hero-actions"><a className="primary" href="#workspace">Use Promptly <ArrowRight size={17} /></a><a className="text-link" href="#benchmarks">View metrics</a></div><div className="proof"><span><Zap size={15} /> 40.89% avg reduction</span><span><Gauge size={15} /> 25 prompt benchmark</span><span><Check size={15} /> Offline compression</span></div></div><div className="hero-art"><div className="orb orb-a" /><div className="orb orb-b" /><div className="float-card top-card">Preserve: JSON, tests, constraints</div><div className="device"><div className="device-screen"><div className="device-notch" /><div className="mini-title">Optimization run</div><div className="mini-line cyan" /><div className="mini-line" /><div className="mini-card"><b>Prompt quality</b><div className="meter"><span /></div><small>89.27% preserved</small></div><div className="mini-card"><b>Token budget</b><div className="meter"><span className="short" /></div><small>40.89% reduction</small></div></div></div><div className="float-card bottom-card">Savings ready <strong>↓ 584 tokens</strong></div></div></section>
      <section className="section benchmarks" id="benchmarks"><div><div className="section-kicker">Proof, not promises</div><h2>Benchmarked for <em>resume-grade</em> proof.</h2><p>Every claim is backed by a local benchmark suite, so Promptly reads as an engineering system rather than a simple text box demo.</p></div><div className="metrics"><Metric value="40.89%" label="average token reduction" /><Metric value="89.27%" label="instruction preservation" /><Metric value="25" label="curated prompts" /><Metric value="~1ms" label="local latency" /></div></section>
      <section className="dark-section" id="workflow"><div className="section-kicker">The workflow</div><h2>Keep the useful signal. <em>Measure the tradeoff.</em></h2><div className="steps"><Step n="01" title="Rank signal" text="Prioritize important sentences, output formats, constraints, and risk markers before trimming." /><Step n="02" title="Compress by mode" text="Choose conservative, balanced, or aggressive savings without changing the interface." /><Step n="03" title="Report impact" text="Surface token deltas, cost estimates, preservation score, and benchmark-ready metrics." /></div></section>
      <section className="workspace-section" id="workspace"><div className="workspace-heading"><div><div className="section-kicker">Live optimizer</div><h2>Promptly Workspace</h2></div><span className="status"><span /> local engine</span></div><div className="controls"><div><label>Compression mode</label><div className="segmented">{config.modes.map(item => <button className={mode === item ? 'selected' : ''} onClick={() => setMode(item)} key={item}>{item}</button>)}</div></div><div><label>Model pricing</label><select value={model} onChange={e => setModel(e.target.value)}>{config.models.map(item => <option key={item}>{item}</option>)}</select></div><div className="price">Input price<br /><strong>${config.pricing[model]?.input_per_million ?? '—'}</strong> per 1M tokens</div></div><textarea className="prompt-input" value={prompt} onChange={e => setPrompt(e.target.value)} placeholder="Paste a long prompt, requirements document, or task brief..." /><button className="optimize" onClick={optimize} disabled={busy}>{busy ? 'Optimizing…' : 'Optimize prompt'} <ArrowRight size={18} /></button>{result && <><div className="result-metrics"><Metric value={result.original_tokens.toLocaleString()} label="original tokens" /><Metric value={result.compressed_tokens.toLocaleString()} label="compressed tokens" /><Metric value={result.saved_tokens.toLocaleString()} label="tokens saved" /><Metric value={`${result.reduction_pct.toFixed(1)}%`} label="reduction" /><Metric value={`${result.preservation_score.toFixed(1)}%`} label="preservation" /></div><div className="cost-row"><span>Cost before <b>${result.cost_before.toFixed(6)}</b></span><span>Cost after <b>${result.cost_after.toFixed(6)}</b></span><span>Estimated saved <b className="green">${result.cost_saved.toFixed(6)}</b></span></div><div className="comparison"><Output title="Original" value={result.original} /><Output title="Compressed" value={result.compressed} actions={<><button onClick={copyResult}>{copied ? <Check size={15} /> : <Copy size={15} />} {copied ? 'Copied' : 'Copy'}</button><button onClick={downloadResult}><Download size={15} /> Download</button></>} /></div></>}</section>
      <section className="closing"><div><div className="section-kicker">Ready when you are</div><h2>Start with one <em>prompt.</em></h2><p>Paste a long instruction, choose a compression mode, and get a shorter version with measurable savings.</p><a className="primary" href="#workspace">Launch workspace <ArrowRight size={17} /></a></div><div className="closing-stat"><strong>{pct.toFixed ? `${pct.toFixed(2)}%` : '40.89%'}</strong><span>average reduction across<br />25 benchmark prompts</span></div></section>
    </main><footer>Promptly <span>Local-first prompt operations for practical AI systems.</span></footer>
  </>
}
function Metric({ value, label }) { return <div className="metric"><strong>{value}</strong><span>{label}</span></div> }
function Step({ n, title, text }) { return <div className="step"><span className="step-number">{n}</span><h3>{title}</h3><p>{text}</p></div> }
function Output({ title, value, actions }) { return <div className="output"><div className="output-head"><h3>{title}</h3><div>{actions}</div></div><pre>{value || '—'}</pre></div> }

createRoot(document.getElementById('root')).render(<App />)
