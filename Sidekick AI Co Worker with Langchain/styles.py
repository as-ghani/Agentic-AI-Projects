import gradio as gr

SOOT = "#141010"        
IRON = "#1D1817"        
ASH = "#2E2624"         
EMBER = "#E4443A"      
COAL_RED = "#8E201A"    
BONE = "#EDE5E2"        
SMOKE = "#9A8D89"       

EMBER_RAMP = gr.themes.Color(
    c50="#FDF1F0", c100="#F9D6D3", c200="#F2ADA8", c300="#EC847D", c400="#E86259",
    c500="#E4443A", c600="#C32F26", c700="#8E201A", c800="#651512", c900="#420D0B",
    c950="#260706",
)

SOOT_RAMP = gr.themes.Color(
    c50="#F5F1F0", c100="#E2DAD8", c200="#C3B7B3", c300="#9A8D89", c400="#736764",
    c500="#564C4A", c600="#3E3634", c700="#2E2624", c800="#1D1817", c900="#141010",
    c950="#0D0A0A",
)

THEME = gr.themes.Base(
    primary_hue=EMBER_RAMP,
    secondary_hue=EMBER_RAMP,
    neutral_hue=SOOT_RAMP,
    font=[gr.themes.GoogleFont("Archivo"), "ui-sans-serif", "system-ui", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("IBM Plex Mono"), "ui-monospace", "monospace"],
).set(
    body_background_fill=SOOT,
    body_text_color=BONE,
    body_text_color_subdued=SMOKE,
    background_fill_primary=IRON,
    background_fill_secondary=SOOT,
    block_background_fill=IRON,
    block_border_color=ASH,
    block_border_width="1px",
    block_label_text_color=SMOKE,
    block_title_text_color=SMOKE,
    block_radius="10px",
    border_color_primary=ASH,
    input_background_fill="#191413",
    input_border_color=ASH,
    input_border_color_focus=COAL_RED,
    input_placeholder_color="#6F6360",
    input_radius="8px",
    button_large_radius="8px",
    button_small_radius="8px",
    button_primary_background_fill=EMBER,
    button_primary_background_fill_hover="#F0574D",
    button_primary_text_color="#160B0A",
    button_secondary_background_fill="transparent",
    button_secondary_background_fill_hover="#241D1C",
    button_secondary_text_color=SMOKE,
    button_secondary_border_color=ASH,
    block_shadow="none",
    shadow_drop="none",
)

CSS = """
.gradio-container {
    background: #141010 !important;
    max-width: 1180px !important;
    padding-left: 34px !important;
}

/* The rail runs the height of the window and reports what the Sidekick is doing.
   The timer owns it, so it updates while a turn is still running. */
#rail {
    position: fixed; top: 0; bottom: 0; left: 0; width: 4px; z-index: 40;
    background: #2E2624;
}
#rail.working { background: linear-gradient(180deg, #8E201A 0%, #E4443A 50%, #8E201A 100%); }
#rail.waiting { background: #E4443A; box-shadow: 0 0 18px rgba(228, 68, 58, 0.75); }
@media (prefers-reduced-motion: no-preference) {
    #rail.waiting { animation: rail-pulse 1.6s ease-in-out infinite; }
}
@keyframes rail-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.45; }
}

#masthead { padding: 26px 0 18px; }
#masthead h1 {
    color: #EDE5E2; font-size: 34px; font-weight: 700; letter-spacing: -0.02em;
    margin: 0; line-height: 1;
}
#masthead p { color: #9A8D89; font-size: 14px; margin: 8px 0 0; max-width: 46ch; }

#status-line {
    font-family: "IBM Plex Mono", ui-monospace, monospace;
    font-size: 12px; color: #6F6360; padding: 0 0 14px;
}
#status-line .dot {
    display: inline-block; width: 6px; height: 6px; margin-right: 8px;
    background: #2E2624; position: relative; top: -1px;
}
#status-line.working .dot, #status-line.waiting .dot { background: #E4443A; }
#status-line.waiting { color: #E4443A; }

#chat { border: 1px solid #2E2624 !important; background: #1D1817 !important; }
#chat .message { font-size: 14px; line-height: 1.55; color: #EDE5E2; }
#chat .message.user {
    background: #241D1C !important; border: 1px solid #3E3634 !important; color: #EDE5E2 !important;
}
#chat .message.user * { color: #EDE5E2 !important; }
#chat .message a { color: #E4443A; }
#chat .message code {
    background: #2E2624 !important; color: #F2ADA8 !important;
    border-radius: 4px; padding: 1px 5px;
}
#chat .message pre code { padding: 10px; display: block; }

#plan {
    background: #1D1817; border: 1px solid #2E2624; border-radius: 10px;
    padding: 18px 18px 20px; height: 100%;
}
#plan h3 { color: #EDE5E2; font-size: 14px; font-weight: 600; margin: 0 0 4px; }
#plan .empty { color: #6F6360; font-size: 13px; line-height: 1.5; margin: 10px 0 0; }
#plan ol { list-style: none; padding: 0; margin: 14px 0 0; }
#plan li {
    display: flex; gap: 10px; align-items: baseline;
    color: #C3B7B3; font-size: 13px; line-height: 1.5;
    padding: 7px 0 7px 12px; border-left: 2px solid #2E2624;
}
#plan .mark { flex: none; width: 8px; height: 8px; border: 1px solid #564C4A; }
#plan li.in_progress { color: #EDE5E2; border-left-color: #E4443A; }
#plan li.in_progress .mark { border-color: #E4443A; background: #E4443A; }
#plan li.completed { color: #6F6360; }
#plan li.completed .mark { border-color: #8E201A; background: #8E201A; }

#ask { background: transparent; border: none; gap: 8px; }
#ask textarea { font-size: 14px; color: #EDE5E2; }

#controls { margin-top: 14px; gap: 10px; }
#start-button { font-weight: 600; }
#start-button:disabled { opacity: 0.4; }
#continue-button {
    background: transparent !important; color: #E4443A !important;
    border: 1px solid #E4443A !important; font-weight: 600;
}
#continue-button:hover { background: rgba(228, 68, 58, 0.12) !important; }

:focus-visible { outline: 2px solid #E4443A !important; outline-offset: 2px; }

footer { display: none !important; }
"""

JS = """
<script>
    const url = new URL(window.location);
    if (url.searchParams.get('__theme') !== 'light') {
        url.searchParams.set('__theme', 'light');
        window.location.replace(url.href);
    }
</script>
"""