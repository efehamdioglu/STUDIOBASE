import json
import os
import re

import streamlit as st
from dotenv import load_dotenv

from src.knob import range_knob, select_knob
from src.orchestrator import run_album_pipeline

load_dotenv(override=True)

st.set_page_config(page_title="STUDIOBASE", page_icon="🎚️", layout="centered")

# ---------------------------------------------------------------------------
# RETRO SONY MÜZİK ÇALAR TEMASI
# Streamlit'in kendi bileşenlerini (slider, radio, button, text_input) hiç
# değiştirmeden, sadece CSS ile eski bir hi-fi cihazının kromlu/metalik
# gövdesine, LCD ekranına ve döner potansiyometre (knob) görünümüne
# büründürüyoruz. Fonksiyonellik (sürükleme, tıklama) aynen Streamlit
# widget'larından geliyor; sadece görünüm retro.
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=VT323&family=Outfit:wght@300;400;500;600;700;800&family=Syncopate:wght@700&display=swap');

    html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }

    /* Sayfa arkaplanı: Koyu neumorphic mat yüzey */
    [data-testid="stAppViewContainer"] {
        background-color: #1e222b;
        background-image: 
            radial-gradient(circle at 10% 20%, #1e222b 0%, #14161d 90%);
    }
    [data-testid="stHeader"] { background: transparent; }

    .block-container { padding-top: 1.8rem; max-width: 450px; }

    /* ---- Neumorphic Cihaz Gövdesi (Chassis) ---- */
    .sb-chassis {
        background: #1e222b;
        border-radius: 20px;
        padding: 18px 22px 22px 22px;
        border: 1px solid rgba(255,255,255,0.03);
        box-shadow:
            12px 12px 24px #12151a,
            -12px -12px 24px #2a2f3c,
            inset 1px 1px 0px rgba(255,255,255,0.05);
    }
    .sb-titlebar {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 4px 6px;
        margin-bottom: 12px;
        border-bottom: 1px solid rgba(255,255,255,0.03);
    }
    .sb-titlebar .dot { width: 7px; height: 7px; border-radius: 50%; display: inline-block; }
    .sb-titlebar .dot.red { background: #ff5f56; box-shadow: 0 0 4px rgba(255,95,86,0.4); }
    .sb-titlebar .dot.yellow { background: #ffbd2e; box-shadow: 0 0 4px rgba(255,189,46,0.4); }
    .sb-titlebar .dot.green { background: #27c93f; box-shadow: 0 0 4px rgba(39,201,63,0.4); }
    .sb-titlebar .name {
        font-family: 'Outfit', sans-serif; font-size: 0.65rem; letter-spacing: 1.5px;
        color: #6c7a9c; margin-left: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        font-weight: 500; text-transform: uppercase;
    }

    /* ---- Marka plakası ---- */
    .sb-brandplate {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 4px 2px 12px 2px;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        margin-bottom: 14px;
    }
    .sb-brand {
        font-family: 'Syncopate', sans-serif;
        font-weight: 700;
        font-size: 1.15rem;
        letter-spacing: 3px;
        color: #f0f2f5;
        text-shadow: 1px 1px 0px rgba(0,0,0,0.4);
    }
    .sb-brand span {
        color: #00e5ff;
        text-shadow: 0 0 8px rgba(0,229,255,0.5);
    }
    .sb-subbrand {
        font-family: 'Outfit', sans-serif;
        font-weight: 500;
        font-size: 0.52rem;
        letter-spacing: 2px;
        color: #6c7a9c;
        margin-top: 2px;
        text-transform: uppercase;
    }
    .sb-led {
        width: 10px; height: 10px; border-radius: 50%;
        background: radial-gradient(circle at 35% 30%, #00ffff, #008b8b 80%);
        box-shadow: 0 0 10px 2px rgba(0,255,255,0.8), inset 0 0 2px rgba(0,0,0,0.5);
        margin-right: 6px;
        display: inline-block;
        animation: sb-pulse 2s ease-in-out infinite;
    }
    .sb-led-off {
        width: 10px; height: 10px; border-radius: 50%;
        background: #2a2f3c;
        box-shadow: inset 1px 1px 2px rgba(0,0,0,0.6);
        display: inline-block;
        margin-right: 6px;
    }
    @keyframes sb-pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.55; } }

    /* ---- LCD ekran paneli (Recessed) ---- */
    .sb-lcd-frame {
        background: #1e222b;
        border-radius: 12px;
        padding: 2px;
        box-shadow:
            inset 3px 3px 6px #12151a,
            inset -3px -3px 6px #2a2f3c;
        margin-bottom: 8px;
        border: 1px solid rgba(255,255,255,0.02);
    }
    .sb-lcd {
        background: rgba(14, 16, 21, 0.55);
        border-radius: 10px;
        padding: 12px 16px;
        font-family: 'VT323', monospace;
        color: #00e5ff;
        text-shadow: 0 0 6px rgba(0,229,255,0.65);
        font-size: 1.25rem;
        line-height: 1.4;
        min-height: 36px;
        box-shadow: inset 2px 2px 5px rgba(0,0,0,0.4);
        letter-spacing: 0.8px;
    }
    .sb-lcd-label {
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        font-size: 0.62rem;
        letter-spacing: 2px;
        color: #8c96a8;
        margin: 14px 2px 6px 2px;
        text-transform: uppercase;
    }

    /* Tema input'unu LCD ekranın içine gömülü göster */
    .sb-lcd-input {
        background: #1e222b;
        border-radius: 12px;
        padding: 2px;
        box-shadow:
            inset 3px 3px 6px #12151a,
            inset -3px -3px 6px #2a2f3c;
        margin-bottom: 8px;
        border: 1px solid rgba(255,255,255,0.02);
    }
    .sb-lcd-input [data-testid="stTextInput"] input {
        background: rgba(14, 16, 21, 0.55) !important;
        color: #00e5ff !important;
        font-family: 'VT323', monospace !important;
        font-size: 1.35rem !important;
        border: none !important;
        box-shadow: none !important;
        text-shadow: 0 0 6px rgba(0,229,255,0.65);
        caret-color: #00e5ff;
        padding: 10px 14px !important;
        height: auto !important;
    }
    .sb-lcd-input [data-testid="stTextInput"] > div {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    .sb-lcd-input [data-testid="stTextInput"] label { display: none; }

    iframe[title="studiobase_knob.studiobase_knob"] { background: transparent; }

    /* ---- Büyük Neumorphic PLAY Butonu ---- */
    div[data-testid="stButton"] button {
        background: #1e222b !important;
        color: #00e5ff !important;
        border: 1px solid rgba(0,229,255,0.2) !important;
        border-radius: 12px !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: 2px !important;
        font-size: 0.88rem !important;
        padding: 0.8rem 0 !important;
        text-shadow: 0 0 4px rgba(0,229,255,0.3) !important;
        box-shadow:
            5px 5px 10px #12151a,
            -5px -5px 10px #2a2f3c,
            inset 1px 1px 0px rgba(255,255,255,0.05) !important;
        transition: all 0.2s ease !important;
        text-transform: uppercase !important;
    }
    div[data-testid="stButton"] button:hover {
        color: #ffffff !important;
        border-color: #00e5ff !important;
        box-shadow:
            6px 6px 12px #111318,
            -6px -6px 12px #2c323f,
            inset 1px 1px 0px rgba(255,255,255,0.08),
            0 0 10px rgba(0,229,255,0.25) !important;
    }
    div[data-testid="stButton"] button:active {
        transform: scale(0.98) !important;
        box-shadow:
            inset 3px 3px 6px #12151a,
            inset -3px -3px 6px #2a2f3c !important;
    }

    /* ---- Neumorphic Parça Kartları ---- */
    .sb-track-card {
        background: #1e222b;
        border: 1px solid rgba(255,255,255,0.03);
        border-radius: 14px;
        padding: 14px 16px;
        margin-top: 15px;
        margin-bottom: 12px;
        box-shadow:
            6px 6px 12px #12151a,
            -6px -6px 12px #2a2f3c,
            inset 1px 1px 0px rgba(255,255,255,0.05);
    }
    .sb-track-card b {
        color: #f0f2f5;
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 0.95rem;
        letter-spacing: 0.5px;
    }

    /* Streamlit TextArea'ları Neumorphic Inset yapma */
    div[data-testid="stTextArea"] textarea {
        background: rgba(14, 16, 21, 0.45) !important;
        color: #e2e8f0 !important;
        border: none !important;
        border-radius: 10px !important;
        box-shadow:
            inset 2px 2px 5px #0d0f13,
            inset -2px -2px 5px #262b36 !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 0.85rem !important;
        padding: 10px 14px !important;
    }
    div[data-testid="stTextArea"] > div {
        background: transparent !important;
        border: none !important;
    }

    /* ---- Ajan Pipeline Paneli ---- */
    .sb-pipeline {
        background: #191c23;
        border-radius: 14px;
        padding: 16px 14px;
        margin-bottom: 14px;
        border: 1px solid rgba(255,255,255,0.02);
        box-shadow:
            inset 4px 4px 8px #12151a,
            inset -4px -4px 8px #222630;
    }
    .sb-pipeline-row { display: flex; align-items: center; justify-content: center; gap: 10px; }
    .sb-pnode {
        flex: 1;
        text-align: center;
        font-family: 'Outfit', sans-serif;
        font-size: 0.6rem;
        font-weight: 700;
        letter-spacing: 1px;
        color: #6c7a9c;
        background: #1e222b;
        border: 1px solid rgba(255,255,255,0.02);
        border-radius: 10px;
        padding: 10px 6px;
        box-shadow:
            3px 3px 6px #12151a,
            -3px -3px 6px #2a2f3c;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .sb-pnode .icon { font-size: 1.3rem; display: block; margin-bottom: 4px; }
    .sb-pnode.active {
        color: #ffffff;
        border-color: var(--glow, #00e5ff);
        box-shadow:
            0 0 15px var(--glow, rgba(0,229,255,0.4)),
            inset 0 0 0 1px var(--glow, #00e5ff);
        animation: sb-node-pulse 1.5s ease-in-out infinite;
    }
    .sb-pnode.done {
        color: #00ff88;
        border-color: rgba(0,255,136,0.3);
        box-shadow: inset 1px 1px 2px rgba(0,255,136,0.1);
    }
    @keyframes sb-node-pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.65; } }
    .sb-parrow-v { text-align: center; color: #4a5468; font-size: 1.1rem; line-height: 1; margin: 4px 0; }
    .sb-ploop { display: flex; flex-direction: column; align-items: center; justify-content: center; min-width: 45px; }
    .sb-ploop-icon { font-size: 1.1rem; color: #ff9e00; text-shadow: 0 0 5px rgba(255,158,0,0.5); }
    .sb-ploop-badge {
        font-family: 'VT323', monospace; font-size: 0.75rem; color: #ff9e00; margin-top: 2px; white-space: nowrap;
        text-shadow: 0 0 4px rgba(255,158,0,0.4);
    }

    /* ---- Ajan Konuşma Kartları (Gömülü Scroll Paneli ile) ---- */
    .sb-log-container {
        max-height: 300px;
        overflow-y: auto;
        padding: 8px;
        background: rgba(14, 16, 21, 0.35);
        border-radius: 12px;
        box-shadow:
            inset 3px 3px 6px #12151a,
            inset -3px -3px 6px #2a2f3c;
        border: 1px solid rgba(255,255,255,0.02);
    }
    .sb-log-container::-webkit-scrollbar {
        width: 6px;
    }
    .sb-log-container::-webkit-scrollbar-track {
        background: transparent;
    }
    .sb-log-container::-webkit-scrollbar-thumb {
        background: #2a2f3c;
        border-radius: 10px;
    }
    .sb-log-container::-webkit-scrollbar-thumb:hover {
        background: #3a4154;
    }

    .sb-msg {
        border-left: 4px solid #4a5468;
        background: #1e222b;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
        font-family: 'Outfit', sans-serif;
        font-size: 0.75rem;
        color: #e2e8f0;
        line-height: 1.4;
        box-shadow:
            3px 3px 6px #12151a,
            -3px -3px 6px #2a2f3c,
            inset 1px 1px 0px rgba(255,255,255,0.02);
    }
    .sb-msg .agent {
        font-weight: 700; letter-spacing: 1px; display: block; margin-bottom: 4px; font-size: 0.65rem;
        text-transform: uppercase;
    }
    .sb-msg .body { color: #cbd5e1; }
    .sb-msg.director { border-left-color: #00e5ff; } .sb-msg.director .agent { color: #00e5ff; text-shadow: 0 0 4px rgba(0,229,255,0.2); }
    .sb-msg.lyricist { border-left-color: #d500f9; } .sb-msg.lyricist .agent { color: #d500f9; text-shadow: 0 0 4px rgba(213,0,249,0.2); }
    .sb-msg.critic-pending { border-left-color: #ff9e00; opacity: 0.85; } .sb-msg.critic-pending .agent { color: #ff9e00; }
    .sb-msg.critic-ok { border-left-color: #00ff88; } .sb-msg.critic-ok .agent { color: #00ff88; text-shadow: 0 0 4px rgba(0,255,136,0.2); }
    .sb-msg.critic-revise { border-left-color: #ff9e00; } .sb-msg.critic-revise .agent { color: #ff9e00; text-shadow: 0 0 4px rgba(255,158,0,0.2); }
    .sb-msg.visual { border-left-color: #ff007f; } .sb-msg.visual .agent { color: #ff007f; text-shadow: 0 0 4px rgba(255,0,127,0.2); }
    .sb-msg.divider {
        background: transparent; border-left: none; text-align: center;
        color: #6c7a9c; font-size: 0.65rem; letter-spacing: 1.5px; padding: 12px 0 6px 0;
        box-shadow: none; font-weight: 600; text-transform: uppercase;
    }
    .sb-msg .verdict-json {
        font-family: 'VT323', monospace; font-size: 0.85rem; color: #00ff88;
        background: rgba(14,16,21,0.6); border-radius: 6px; padding: 4px 8px; margin-top: 6px;
        box-shadow: inset 1px 1px 3px rgba(0,0,0,0.4);
        border: 1px solid rgba(0,255,136,0.15);
    }

    /* ---- Streamlit Tabs Neumorphism ---- */
    div[data-testid="stTabBar"] {
        background: #1e222b;
        padding: 4px;
        border-radius: 12px;
        box-shadow:
            inset 2px 2px 5px #12151a,
            inset -2px -2px 5px #2a2f3c;
        border: 1px solid rgba(255,255,255,0.02);
        gap: 4px;
        margin-top: 10px;
    }
    button[data-baseweb="tab"] {
        background: transparent !important;
        color: #6c7a9c !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 6px 12px !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background: #1e222b !important;
        color: #00e5ff !important;
        box-shadow:
            3px 3px 6px #12151a,
            -3px -3px 6px #2a2f3c !important;
    }

    /* ---- Streamlit Expander Neumorphism ---- */
    div[data-testid="stExpander"] {
        background: #1e222b !important;
        border: 1px solid rgba(255,255,255,0.03) !important;
        border-radius: 12px !important;
        box-shadow:
            3px 3px 6px #12151a,
            -3px -3px 6px #2a2f3c !important;
        overflow: hidden;
        margin-top: 8px;
    }
    div[data-testid="stExpander"] details summary {
        background: transparent !important;
        color: #f0f2f5 !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 500 !important;
    }

    /* ---- Streamlit Code Block Neumorphism ---- */
    div[data-testid="stCodeBlock"] {
        background: #1e222b !important;
        border: 1px solid rgba(255,255,255,0.02) !important;
        border-radius: 12px !important;
        box-shadow:
            inset 3px 3px 6px #12151a,
            inset -3px -3px 6px #2a2f3c !important;
        padding: 4px !important;
    }
    div[data-testid="stCodeBlock"] pre {
        background: transparent !important;
        border: none !important;
    }

    [data-testid="stMarkdownContainer"] p { color: #cbd5e1; }

    /* ---- Apple-style Segmented Control (st.radio horizontal) ---- */
    .sb-toggle-label {
        font-family: 'Outfit', sans-serif;
        font-size: 0.58rem; letter-spacing: 1.5px; color: #8c96a8; font-weight: 600;
        margin-top: 4px; margin-bottom: 6px; text-transform: uppercase; text-align: center;
        text-shadow: 1px 1px 0px rgba(0,0,0,0.2);
    }
    div[role="radiogroup"] {
        background: #14161d !important;
        border-radius: 10px !important;
        padding: 3px !important;
        border: 1px solid rgba(255,255,255,0.02) !important;
        box-shadow: inset 2px 2px 4px #0c0e12, inset -2px -2px 4px #222630 !important;
        display: flex !important;
        flex-direction: row !important;
        width: 100% !important;
        gap: 0px !important;
    }
    div[role="radiogroup"] label {
        flex: 1 !important;
        text-align: center !important;
        justify-content: center !important;
        background: transparent !important;
        border-radius: 8px !important;
        padding: 6px 4px !important;
        margin: 0 !important;
        color: #6c7a9c !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        cursor: pointer !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        display: flex !important;
        align-items: center !important;
        white-space: nowrap !important;
    }
    div[role="radiogroup"] label * {
        white-space: nowrap !important;
        word-break: keep-all !important;
    }
    div[role="radiogroup"] label > div {
        margin: 0 !important;
        padding: 0 !important;
    }
    /* Hide the radio circle & indicator completely under all Streamlit versions */
    div[role="radiogroup"] label > div:first-child,
    div[role="radiogroup"] label div[role="presentation"],
    div[role="radiogroup"] label [class*="StyledRadioCircle"],
    div[role="radiogroup"] label [class*="RadioCircle"],
    div[role="radiogroup"] label [class*="RadioIcon"],
    div[role="radiogroup"] label [class*="RadioDot"],
    div[role="radiogroup"] label [class*="RadioSelect"],
    div[role="radiogroup"] label span[role="presentation"] {
        display: none !important;
        width: 0 !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        opacity: 0 !important;
    }
    /* Active State (Apple-style sliding segment capsule) */
    div[role="radiogroup"] label:has(input:checked) {
        background: #1e222b !important;
        color: #00e5ff !important;
        box-shadow:
            3px 3px 6px #0c0e12,
            -3px -3px 6px #282e3a,
            inset 1px 1px 0px rgba(255,255,255,0.05) !important;
    }
    div[role="radiogroup"] label:hover {
        color: #f0f2f5 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9ğüşıöç\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text)
    return text or "album"


class StreamlitProgressReporter:
    """Orkestratörün on_progress callback'ini alıp canlı olarak Streamlit
    arayüzüne yazan köprü. İki şeyi eş zamanlı günceller:
    1) Ajan Pipeline diyagramı — hangi ajan şu an aktif, Söz Yazarı <->
       Eleştirmen geri bildirim döngüsü ve iterasyon sayacı canlı görünür.
    2) Ajan konuşma kartları — her ajanın ne söylediği/karar verdiği, renk
       kodlu ve Eleştirmen'in yapılandırılmış JSON kararı açıkça gösterilir
       (dinamik yönlendirmenin koddan değil modelin çıktısından geldiğini
       kanıtlamak için)."""

    def __init__(self, pipeline_placeholder, log_placeholder, track_containers):
        self.pipeline_placeholder = pipeline_placeholder
        self.log_placeholder = log_placeholder
        self.track_containers = track_containers
        self.messages: list[str] = []
        self.active_node: str | None = None
        self.done_nodes: set[str] = set()
        self.iteration = 0
        self.max_iterations = 0
        self.last_critic_ok = True
        self._render_pipeline()

    # -- render yardımcıları -------------------------------------------------

    def _render_log(self) -> None:
        html = (
            f'<div class="sb-log-container" id="sb-log-win">'
            f'{"".join(self.messages[-50:])}'
            f'</div>'
            f'<script>'
            f'  var el = document.getElementById("sb-log-win");'
            f'  if (el) {{ el.scrollTop = el.scrollHeight; }}'
            f'</script>'
        )
        self.log_placeholder.markdown(html, unsafe_allow_html=True)

    def _msg(self, css_class: str, agent_label: str, icon: str, body_html: str) -> None:
        self.messages.append(
            f'<div class="sb-msg {css_class}"><span class="agent">{icon} {agent_label}</span>'
            f'<span class="body">{body_html}</span></div>'
        )
        self._render_log()

    def _divider(self, text: str) -> None:
        self.messages.append(f'<div class="sb-msg divider">{text}</div>')
        self._render_log()

    def _render_pipeline(self) -> None:
        def node(key: str, icon: str, label: str, glow: str) -> str:
            cls = "sb-pnode"
            style = ""
            if key == self.active_node:
                cls += " active"
                style = f' style="--glow:{glow}"'
            elif key in self.done_nodes:
                cls += " done"
            return f'<div class="{cls}"{style}><span class="icon">{icon}</span>{label}</div>'

        critic_glow = "#22c55e" if self.last_critic_ok else "#f59e0b"
        loop_badge = f"İTR {self.iteration}/{self.max_iterations}" if self.max_iterations else "—"
        html = (
            '<div class="sb-pipeline">'
            + node("director", "🎬", "DİREKTÖR", "#3b82f6")
            + '<div class="sb-parrow-v">↓</div>'
            + '<div class="sb-pipeline-row">'
            + node("lyricist", "✍️", "SÖZ YAZARI", "#8b5cf6")
            + f'<div class="sb-ploop"><div class="sb-ploop-icon">⟲</div><div class="sb-ploop-badge">{loop_badge}</div></div>'
            + node("critic", "🎯", "ELEŞTİRMEN", critic_glow)
            + "</div>"
            + '<div class="sb-parrow-v">↓</div>'
            + node("visual", "🎨", "GÖRSEL AJAN", "#ec4899")
            + "</div>"
        )
        self.pipeline_placeholder.markdown(html, unsafe_allow_html=True)

    # -- olay işleyici --------------------------------------------------------

    def __call__(self, event: str, **kwargs) -> None:
        if event == "director_start":
            self.active_node = "director"
            self._render_pipeline()
            self._msg(
                "director", "KREATİF DİREKTÖR", "🎬",
                f"Tema alındı: <b>{kwargs['theme']}</b> — {kwargs['n_tracks']} parçalık "
                f"tracklist planlanıyor…",
            )
        elif event == "director_done":
            self.done_nodes.add("director")
            self.active_node = None
            self._render_pipeline()
            self._msg(
                "director", "KREATİF DİREKTÖR", "🎬",
                f"Albüm başlığına karar verdim: <b>{kwargs['album_title']}</b>",
            )
        elif event == "track_start":
            track = kwargs["track"]
            self.iteration = 0
            self.max_iterations = 0
            self.done_nodes.discard("lyricist")
            self.done_nodes.discard("critic")
            self._divider(
                f"— Parça {kwargs['index']}/{kwargs['total']}: {track.title} "
                f"({track.mood}) —"
            )
        elif event == "lyricist_start":
            self.active_node = "lyricist"
            self.iteration = kwargs["iteration"]
            self.max_iterations = kwargs["max_iterations"]
            self._render_pipeline()
            if kwargs["iteration"] > 1:
                note = "Eleştirmenin geri bildirimini dikkate alarak sözü revize ediyorum…"
            else:
                note = "İlk taslağı yazıyorum…"
            self._msg(
                "lyricist", "SÖZ YAZARI", "✍️",
                f"İterasyon {kwargs['iteration']}/{kwargs['max_iterations']}: {note}",
            )
        elif event == "lyricist_done":
            self.done_nodes.add("lyricist")
            preview = kwargs["track"].current_lyrics.strip().split("\n")[0][:50]
            self._msg("lyricist", "SÖZ YAZARI", "✍️", f"Taslak hazır → <i>“{preview}…”</i>")
        elif event == "critic_start":
            self.active_node = "critic"
            self._render_pipeline()
            self._msg(
                "critic-pending", "ELEŞTİRMEN", "🎯",
                "Hece ölçüsü, kafiye ve akıcılığı değerlendiriyorum…",
            )
        elif event == "track_iteration":
            verdict = kwargs["verdict"]
            self.last_critic_ok = verdict["approved"]
            self.done_nodes.add("critic")
            self.active_node = None
            self._render_pipeline()
            cls = "critic-ok" if verdict["approved"] else "critic-revise"
            durum = "✅ ONAYLANDI" if verdict["approved"] else "🔁 REVİZYON İSTENDİ"
            routing = (
                "parça finalize ediliyor"
                if verdict["approved"]
                else "söz yazarına geri dönülüyor (dinamik yönlendirme)"
            )
            verdict_json = (
                f'approved={str(verdict["approved"]).lower()} · '
                f'issues={len(verdict["issues"])} · → {routing}'
            )
            self._msg(
                cls, "ELEŞTİRMEN", "🎯",
                f"{durum} — <i>{verdict['feedback']}</i>"
                f'<div class="verdict-json">{verdict_json}</div>',
            )
        elif event == "track_done":
            track = kwargs["track"]
            container = self.track_containers[kwargs["index"] - 1]
            with container:
                st.markdown(
                    f'<div class="sb-track-card"><b>▶ {track.title}</b><br>'
                    f'<span style="font-size:0.8rem;color:#8c96a8;">Mood: {track.mood} — '
                    f"{track.status} ({track.iterations_used} iterasyon)</span></div>",
                    unsafe_allow_html=True,
                )
                st.text_area(
                    "Şarkı Sözü",
                    value=track.current_lyrics,
                    height=220,
                    key=f"lyrics_{kwargs['index']}",
                    label_visibility="collapsed",
                )
                if track.critic_feedback_history:
                    with st.expander("Revizyon Geçmişi"):
                        for entry in track.critic_feedback_history:
                            verdict_text = "Onaylandı" if entry.approved else "Revizyon istendi"
                            st.markdown(f"- İterasyon {entry.iteration}: **{verdict_text}** — {entry.feedback}")
        elif event == "visual_start":
            self.active_node = "visual"
            self._render_pipeline()
            self._msg("visual", "GÖRSEL STİL AJANI", "🎨", "Albüm kapağı için görsel prompt üretiyorum…")
        elif event == "visual_done":
            self.done_nodes.add("visual")
            self.active_node = None
            self._render_pipeline()
            self._msg("visual", "GÖRSEL STİL AJANI", "🎨", "Tamamlandı.")


# ---------------------------------------------------------------------------
# CİHAZ ÖN PANELİ
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="sb-chassis">
        <div class="sb-titlebar">
            <span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span>
            <span class="name">STUDIOBASE.vst</span>
        </div>
        <div class="sb-brandplate">
            <div>
                <div class="sb-brand">STUDIO<span>BASE</span></div>
                <div class="sb-subbrand">MULTI-AGENT MUSIC ENGINE</div>
            </div>
            <div><span class="sb-led"></span></div>
        </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="sb-lcd-label">ALBÜM TEMASI</div>', unsafe_allow_html=True)
st.markdown('<div class="sb-lcd-input">', unsafe_allow_html=True)
theme = st.text_input(
    "Albüm Teması", placeholder="ör. CYBERPUNK MELANKOLİ", label_visibility="collapsed"
)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="sb-lcd-label">KUMANDA PANELİ</div>', unsafe_allow_html=True)

# Knobs Row (PARÇA & REVİZYON)
knob_row_col1, knob_row_col2 = st.columns(2)
with knob_row_col1:
    n_tracks = range_knob("PARÇA", min_value=1, max_value=8, value=4, key="n_tracks_knob")
with knob_row_col2:
    max_iterations = range_knob("REVİZYON", min_value=1, max_value=5, value=3, key="max_iter_knob")

st.markdown('<div style="margin-top: 12px;"></div>', unsafe_allow_html=True)

# Toggles Row (SAĞLAYICI & MODEL)
toggle_row_col1, toggle_row_col2 = st.columns(2)
with toggle_row_col1:
    st.markdown('<div class="sb-toggle-label">SAĞLAYICI</div>', unsafe_allow_html=True)
    provider_options = ["ollama", "gemini", "anthropic"]
    saved_provider = st.session_state.get("provider_value", "gemini")
    default_provider_index = (
        provider_options.index(saved_provider) if saved_provider in provider_options else 0
    )
    provider = st.radio(
        "SAĞLAYICI",
        options=provider_options,
        index=default_provider_index,
        horizontal=True,
        label_visibility="collapsed",
        key="provider_toggle"
    )
    st.session_state["provider_value"] = provider

ollama_models = ["qwen2.5:7b", "qwen2.5-coder:3b"]
gemini_models = ["gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-2.5-flash", "gemini-2.5-pro"]
anthropic_models = ["claude-sonnet-5", "claude-haiku-4-5", "claude-opus-5"]

if provider == "ollama":
    model_options = ollama_models
elif provider == "gemini":
    model_options = gemini_models
else:
    model_options = anthropic_models

friendly_names = {
    "qwen2.5:7b": "Qwen 7B",
    "qwen2.5-coder:3b": "Coder",
    "gemini-3.5-flash-lite": "Gemini 3.5 Lite",
    "gemini-3.6-flash": "Gemini 3.6 Flash",
    "gemini-2.5-flash": "Gemini 2.5 Flash",
    "gemini-2.5-pro": "Gemini Pro",
    "claude-sonnet-5": "Sonnet",
    "claude-haiku-4-5": "Haiku",
    "claude-opus-5": "Opus"
}
friendly_to_tech = {v: k for k, v in friendly_names.items()}
model_friendly_options = [friendly_names.get(m, m) for m in model_options]

model_default = st.session_state.get("model_value")
if model_default not in model_options:
    model_default = model_options[0]
default_friendly = friendly_names.get(model_default, model_default)
default_index = model_friendly_options.index(default_friendly) if default_friendly in model_friendly_options else 0

with toggle_row_col2:
    st.markdown('<div class="sb-toggle-label">MODEL</div>', unsafe_allow_html=True)
    model_friendly = st.radio(
        "MODEL",
        options=model_friendly_options,
        index=default_index,
        horizontal=True,
        label_visibility="collapsed",
        key="model_toggle"
    )
    model = friendly_to_tech.get(model_friendly, model_friendly)
    st.session_state["model_value"] = model

generate_clicked = st.button("▶  PLAY  —  ALBÜM ÜRET", type="primary", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)  # /sb-chassis

# ---------------------------------------------------------------------------
# ÜRETİM VE SONUÇLAR
# ---------------------------------------------------------------------------

if generate_clicked:
    os.environ["LLM_PROVIDER"] = provider
    if provider == "ollama":
        os.environ["OLLAMA_MODEL"] = model
    elif provider == "gemini":
        os.environ["GEMINI_MODEL"] = model
    else:
        os.environ["ANTHROPIC_MODEL"] = model

    if not theme.strip():
        st.error("Lütfen bir albüm teması girin.")
    elif provider == "anthropic" and not os.environ.get("ANTHROPIC_API_KEY"):
        st.error(
            "ANTHROPIC_API_KEY tanımlı değil. Proje kökündeki `.env` dosyasına "
            "API anahtarınızı ekleyin (bkz. `.env.example`)."
        )
    elif provider == "gemini" and not os.environ.get("GEMINI_API_KEY"):
        st.error(
            "GEMINI_API_KEY tanımlı değil. Proje kökündeki `.env` dosyasına "
            "Gemini API anahtarınızı ekleyin (Google AI Studio'dan alabilirsiniz)."
        )
    else:
        st.markdown('<div class="sb-lcd-label">AJAN PIPELINE\'I</div>', unsafe_allow_html=True)
        pipeline_placeholder = st.empty()

        st.markdown('<div class="sb-lcd-label">AJAN KONUŞMA GÜNLÜĞÜ</div>', unsafe_allow_html=True)
        log_placeholder = st.empty()

        st.subheader("🎼 Parçalar")
        track_columns = st.columns(2)
        track_containers = [track_columns[i % 2].container() for i in range(n_tracks)]

        reporter = StreamlitProgressReporter(pipeline_placeholder, log_placeholder, track_containers)

        with st.spinner("Ajanlar çalışıyor..."):
            try:
                print(f"DEBUG: provider={provider}, env={os.environ.get('LLM_PROVIDER')}, gemini_key_set={bool(os.environ.get('GEMINI_API_KEY'))}, anthropic_key_set={bool(os.environ.get('ANTHROPIC_API_KEY'))}")
                album = run_album_pipeline(
                    theme=theme,
                    n_tracks=n_tracks,
                    max_iterations=max_iterations,
                    on_progress=reporter,
                )
            except Exception as exc:  # noqa: BLE001 - kullanıcıya net hata göstermek için
                st.error(f"Üretim sırasında hata oluştu: {exc}")
                st.stop()

        st.success(f"Albüm tamamlandı: **{album.album_title}**")

        if album.cover_art_prompt:
            st.subheader("🎨 Albüm Kapağı Görsel Prompt'u")
            st.info(album.cover_art_prompt)

        slug = slugify(album.album_title or theme)
        markdown_report = album.markdown_report()
        json_report = json.dumps(album.to_dict(), ensure_ascii=False, indent=2)

        st.subheader("📄 Tam Rapor")
        tab_md, tab_json = st.tabs(["Markdown", "JSON (State)"])
        with tab_md:
            st.markdown(markdown_report)
        with tab_json:
            st.code(json_report, language="json")

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "⬇️ Markdown indir",
                data=markdown_report,
                file_name=f"{slug}.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with col2:
            st.download_button(
                "⬇️ JSON indir",
                data=json_report,
                file_name=f"{slug}.json",
                mime="application/json",
                use_container_width=True,
            )
else:
    st.caption("Yukarıdan bir tema girip PLAY'e basın.")
