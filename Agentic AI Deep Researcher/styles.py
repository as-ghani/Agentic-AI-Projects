HEADER_HTML = """
<div class="dr-header">
    <div class="dr-header-badge">Agentic Research</div>
    <h1 class="dr-header-title">Deep Research</h1>
    <p class="dr-header-sub">Ask a question. I'll clarify, search, and write the report.</p>
</div>
"""

EXAMPLES = [
    "What are the latest developments in solid-state batteries?",
    "How is generative AI changing drug discovery?",
    "What's the current state of nuclear fusion research?",
]

JS = """
() => {
    document.title = "Deep Research";
}
"""

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --dr-bg: #0a0908;
    --dr-bg-elev: #16130f;
    --dr-bg-elev-2: #1e1a15;
    --dr-border: #2c2620;
    --dr-text: #f4efe9;
    --dr-text-muted: #a89f95;
    --dr-accent: #ff4620;
    --dr-accent-2: #ff8a3d;
    --dr-accent-glow: rgba(255, 70, 32, 0.35);
}

.gradio-container {
    background: radial-gradient(circle at 20% 0%, #1a120c 0%, var(--dr-bg) 55%) !important;
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    color: var(--dr-text) !important;
}

.dr-header { text-align: center; padding: 2.5rem 1rem 1.5rem; }
.dr-header-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    font-size: 0.72rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--dr-accent-2);
    background: rgba(255, 70, 32, 0.1);
    border: 1px solid rgba(255, 70, 32, 0.35);
    margin-bottom: 0.9rem;
}
.dr-header-title {
    font-size: 2.4rem;
    font-weight: 700;
    margin: 0;
    background: linear-gradient(90deg, #fff 0%, #ffd9c2 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}
.dr-header-sub { color: var(--dr-text-muted); margin-top: 0.5rem; font-size: 0.98rem; }

.dr-query-row {
    max-width: 760px;
    margin: 0 auto 0.5rem;
    background: var(--dr-bg-elev);
    border: 1px solid var(--dr-border);
    border-radius: 16px;
    padding: 0.4rem;
    box-shadow: 0 8px 30px rgba(0,0,0,0.35);
}
#dr-query textarea, #dr-query input {
    background: transparent !important;
    color: var(--dr-text) !important;
    font-size: 1rem !important;
    border: none !important;
}
#dr-run {
    background: linear-gradient(135deg, var(--dr-accent) 0%, var(--dr-accent-2) 100%) !important;
    border: none !important;
    color: #fff !important;
    font-weight: 600 !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 18px var(--dr-accent-glow);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
#dr-run:hover { transform: translateY(-1px); box-shadow: 0 6px 22px var(--dr-accent-glow); }

.dr-examples-label {
    max-width: 760px;
    margin: 1.2rem auto 0.4rem;
    color: var(--dr-text-muted);
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
#dr-examples { max-width: 760px; margin: 0 auto; }
#dr-examples button {
    background: var(--dr-bg-elev) !important;
    border: 1px solid var(--dr-border) !important;
    color: var(--dr-text-muted) !important;
    border-radius: 10px !important;
}
#dr-examples button:hover { border-color: var(--dr-accent) !important; color: var(--dr-text) !important; }

#dr-clarify {
    max-width: 760px;
    margin: 1.5rem auto;
    background: var(--dr-bg-elev);
    border: 1px solid var(--dr-border);
    border-radius: 16px;
    padding: 1.4rem;
    box-shadow: 0 8px 30px rgba(0,0,0,0.3);
}
.dr-clarify-label { font-weight: 600; color: var(--dr-accent-2); margin-bottom: 0.8rem; font-size: 0.95rem; }
.dr-answer textarea, .dr-answer input {
    background: var(--dr-bg-elev-2) !important;
    border: 1px solid var(--dr-border) !important;
    color: var(--dr-text) !important;
    border-radius: 10px !important;
}
.dr-answer label { color: var(--dr-text-muted) !important; }
#dr-submit {
    background: linear-gradient(135deg, var(--dr-accent) 0%, var(--dr-accent-2) 100%) !important;
    border: none !important;
    color: #fff !important;
    font-weight: 600 !important;
    border-radius: 12px !important;
    margin-top: 0.6rem;
    box-shadow: 0 4px 18px var(--dr-accent-glow);
}

#dr-report {
    max-width: 820px;
    margin: 2rem auto;
    background: var(--dr-bg-elev);
    border: 1px solid var(--dr-border);
    border-radius: 16px;
    padding: 1.8rem 2rem;
    line-height: 1.65;
}
#dr-report h1, #dr-report h2, #dr-report h3 { color: var(--dr-accent-2); }
#dr-report a { color: var(--dr-accent); }
"""