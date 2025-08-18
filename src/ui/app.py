#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mini Microcosmos - Minimalist Single Interface
Black theme optimized, sequential persona responses
"""

import json
import os
import asyncio
import sys
import time
import random
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv
import google.generativeai as genai
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

import streamlit as st

# Path setup
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Environment variables
load_dotenv(dotenv_path='config/.env')

# Minimalist page config
st.set_page_config(
    page_title="Mini-Microcosmos",
    page_icon="🎭",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Minimalist Black Theme CSS
st.markdown("""
<style>
/* CSS Variables */
:root {
  --bg-primary: #000000;
  --bg-secondary: #111111;
  --bg-tertiary: #1a1a1a;
  --bg-card: #0a0a0a;

  --text-primary: #ffffff;
  --text-secondary: #e5e5e5;
  --text-muted: #a3a3a3;
  --text-dim: #737373;

  --accent-primary: #3b82f6;
  --accent-secondary: #8b5cf6;
  --accent-success: #10b981;
  --accent-warning: #f59e0b;
  --accent-error: #ef4444;

  --border-color: #262626;
  --border-light: #404040;

  --radius: 0.75rem;
  --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
}

/* Reset */
*, *::before, *::after {
  box-sizing: border-box;
}

/* Hide Streamlit UI */
#MainMenu, footer, .stActionButton, header[data-testid="stHeader"] {
  display: none !important;
}

/* App Base */
.stApp {
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
}

.main .block-container {
  padding: 1rem !important;
  max-width: 800px !important;
}

/* Header */
.app-header {
  text-align: center;
  padding: 2rem 0 1.5rem 0;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 1.5rem;
}

.app-title {
  font-size: 2.25rem;
  font-weight: 700;
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0;
  letter-spacing: -0.02em;
}

.app-subtitle {
  color: var(--text-muted);
  font-size: 0.875rem;
  margin-top: 0.5rem;
  font-weight: 400;
}

/* Status Bar */
.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 0.5rem 1rem;
  margin-bottom: 1rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent-success);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Chat Container - Removed */
/* .chat-container removed as messages display directly */

/* Personas Badge */
.personas-info {
  display: flex;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.persona-badge {
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  padding: 0.5rem 1rem;
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-align: center;
}

.persona-badge.eski {
  border-color: var(--accent-error);
  color: var(--accent-error);
}

.persona-badge.yeni {
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}

/* Chat Messages - Better contrast */
div[data-testid="stChatMessage"] {
  margin-bottom: 1rem !important;
  opacity: 0;
  animation: fadeIn 0.3s ease forwards;
}

@keyframes fadeIn {
  to { opacity: 1; }
}

/* Message Bubbles - High contrast */
div[data-testid="stChatMessage"] > div {
  background: var(--bg-secondary) !important;
  border: 1px solid var(--border-light) !important;
  border-radius: var(--radius) !important;
  padding: 1rem !important;
  color: var(--text-primary) !important;
  box-shadow: var(--shadow) !important;
  max-width: 100% !important;
}

/* User Messages */
div[data-testid="stChatMessage"][data-testid*="user"] > div {
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)) !important;
  color: white !important;
  border: none !important;
}

/* Assistant Messages - High contrast */
div[data-testid="stChatMessage"][data-testid*="assistant"] > div {
  background: var(--bg-tertiary) !important;
  color: var(--text-primary) !important;
  border: 1px solid var(--border-light) !important;
}

/* Message text - Force high contrast */
div[data-testid="stChatMessage"] p,
div[data-testid="stChatMessage"] div,
div[data-testid="stChatMessage"] span {
  color: inherit !important;
  opacity: 1 !important;
}

/* Persona Headers in Messages */
.persona-header-msg {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.1);
}

.persona-header-msg.eski {
  color: var(--accent-error);
  background: rgba(239, 68, 68, 0.1);
}

.persona-header-msg.yeni {
  color: var(--accent-primary);
  background: rgba(59, 130, 246, 0.1);
}

/* Chat Input */
div[data-testid="stChatInput"] > div {
  background: var(--bg-secondary) !important;
  border: 1px solid var(--border-light) !important;
  border-radius: var(--radius) !important;
  transition: border-color 0.2s ease !important;
}

div[data-testid="stChatInput"] > div:focus-within {
  border-color: var(--accent-primary) !important;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
}

div[data-testid="stChatInput"] input {
  background: transparent !important;
  color: var(--text-primary) !important;
  border: none !important;
}

div[data-testid="stChatInput"] input::placeholder {
  color: var(--text-muted) !important;
}

/* Buttons */
.stButton > button {
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)) !important;
  color: white !important;
  border: none !important;
  border-radius: var(--radius) !important;
  font-weight: 500 !important;
  padding: 0.75rem 1.5rem !important;
  transition: all 0.2s ease !important;
  font-size: 0.875rem !important;
}

.stButton > button:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 8px 25px -5px rgba(59, 130, 246, 0.4) !important;
}

/* Control Panel */
.control-panel {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-color);
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

/* Thinking Process */
.streamlit-expanderHeader {
  background: var(--bg-secondary) !important;
  border: 1px solid var(--border-color) !important;
  border-radius: var(--radius) !important;
  color: var(--text-secondary) !important;
  font-size: 0.875rem !important;
}

.streamlit-expanderContent {
  background: var(--bg-primary) !important;
  border: 1px solid var(--border-color) !important;
  border-top: none !important;
  color: var(--text-muted) !important;
  font-size: 0.75rem !important;
  max-height: 200px !important;
  overflow-y: auto !important;
}

/* Alerts */
.stSuccess {
  background: rgba(16, 185, 129, 0.1) !important;
  border: 1px solid var(--accent-success) !important;
  color: var(--accent-success) !important;
  border-radius: var(--radius) !important;
}

.stError {
  background: rgba(239, 68, 68, 0.1) !important;
  border: 1px solid var(--accent-error) !important;
  color: var(--accent-error) !important;
  border-radius: var(--radius) !important;
}

.stInfo {
  background: rgba(59, 130, 246, 0.1) !important;
  border: 1px solid var(--accent-primary) !important;
  color: var(--accent-primary) !important;
  border-radius: var(--radius) !important;
}

/* Loading */
.stSpinner {
  color: var(--accent-primary) !important;
}

/* Scrollbar - Apply to main content */
.main .block-container::-webkit-scrollbar {
  width: 6px;
}

.main .block-container::-webkit-scrollbar-track {
  background: var(--bg-primary);
}

.main .block-container::-webkit-scrollbar-thumb {
  background: var(--border-light);
  border-radius: 3px;
}

/* Mobile */
@media (max-width: 768px) {
  .main .block-container {
    padding: 0.75rem !important;
  }

  .app-title {
    font-size: 1.75rem;
  }

  .personas-info {
    flex-direction: column;
    align-items: center;
  }

  .control-panel {
    flex-direction: column;
  }

  .stButton > button {
    width: 100% !important;
  }
}

/* Force text readability */
* {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>
""", unsafe_allow_html=True)


# Enhanced Agent Class (simplified for this interface)
class MinimalistPersonaAgent:
    def __init__(self, persona_name="tugrul_eski"):
        self.persona_name = persona_name

        # API key management
        self.api_keys = self._load_gemini_keys()
        self.current_api_index = 0

        # Smithery API
        self.smithery_api_key = os.getenv("SMITHERY_API_KEY")
        self.smithery_profile = os.getenv("SMITHERY_PROFILE")

        # Initialize model
        self._initialize_model()

        # Load persona
        self.persona = self._load_persona(persona_name)
        self.conversation_history = []

    def _load_gemini_keys(self) -> List[str]:
        """Load Gemini API keys"""
        api_keys = []

        main_key = os.getenv("GEMINI_API_KEY")
        if main_key:
            api_keys.append(main_key)

        for i in range(1, 15):
            key = os.getenv(f"GEMINI_API_KEY_{i}")
            if key:
                api_keys.append(key)

        if not api_keys:
            raise ValueError("❌ No GEMINI API keys found!")

        random.shuffle(api_keys)
        return api_keys

    def _initialize_model(self):
        """Initialize Gemini model"""
        try:
            genai.configure(api_key=self.api_keys[self.current_api_index])
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            raise Exception(f"Model initialization error: {e}")

    def _load_persona(self, persona_name):
        """Load persona"""
        try:
            persona_path = f'src/personas/{persona_name}.json'
            with open(persona_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            return {
                "name": persona_name.replace('_', ' ').title(),
                "bio": ["Test persona"],
                "style": {"chat": ["Normal konuşur"]},
                "lore": [""],
                "knowledge": [""]
            }

    def switch_api_key(self):
        """Switch API key"""
        self.current_api_index = (self.current_api_index + 1) % len(self.api_keys)
        self._initialize_model()

    async def try_with_rotation(self, prompt: str, max_retries: int = 3) -> str:
        """Try with API rotation"""
        for attempt in range(max_retries):
            try:
                response = await self.model.generate_content_async(prompt)
                return response.text.strip()
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    if attempt < max_retries - 1:
                        self.switch_api_key()
                        continue
                else:
                    raise e
        return "Sistem yoğunluğu nedeniyle geçici olarak hizmet veremiyorum."

    def create_system_prompt(self):
        """Create system prompt"""
        bio_text = "\n- ".join(self.persona.get("bio", ["Bilinmiyor"])[:5])
        style_text = "\n- ".join(self.persona.get("style", {}).get("chat", ["Normal konuşur"])[:3])
        lore_text = "\n- ".join(self.persona.get("lore", [""])[:8])

        return f"""Sen {self.persona["name"]}'sin.

BİOGRAFİ:
- {bio_text}

KONUŞMA TARZI:
- {style_text}

KARAKTERIN:
- {lore_text}

KURALLAR:
- Karakterine uygun davran
- Samimi ve gerçekçi ol
- 2-3 paragraf cevap ver"""

    async def chat(self, user_input: str) -> str:
        """Main chat function"""
        # Check for current topics
        search_triggers = ["son", "güncel", "haber", "gündem", "2024", "2025"]
        needs_search = any(trigger in user_input.lower() for trigger in search_triggers)

        current_date = datetime.now().strftime("%d %B %Y")

        # Build context
        context = ""
        if needs_search and self.smithery_api_key:
            context = "Güncel haberlere erişimin var. "

        # Final prompt
        final_prompt = f"""{self.create_system_prompt()}

BUGÜN: {current_date}
{context}

Kullanıcı: "{user_input}"

Karakterine uygun, detaylı cevap ver:"""

        try:
            response_text = await self.try_with_rotation(final_prompt)

            # Add to history
            self.conversation_history.append({
                'user': user_input,
                'assistant': response_text
            })

            # Keep last 2 conversations
            if len(self.conversation_history) > 2:
                self.conversation_history = self.conversation_history[-2:]

            return response_text

        except Exception as e:
            return "Şu anda teknik sorun yaşıyorum, özür dilerim."


# Session state initialization
def init_session_state():
    """Initialize session state"""
    defaults = {
        "messages": [],
        "processing": False,
        "agents_initialized": False,
        "thinking_logs": []
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def render_header():
    """Render minimalist header"""
    st.markdown("""
    <div class="app-header">
        <h1 class="app-title">Mini-Microcosmos</h1>
        <p class="app-subtitle"> Demo Microcosmos from YEB </p>
    </div>
    """, unsafe_allow_html=True)


def render_personas_info():
    """Render personas information"""
    st.markdown("""
    <div class="personas-info">
        <div class="persona-badge eski">
            🎯 Eski Tuğrul · Milliyetçi · Geleneksel
        </div>
        <div class="persona-badge yeni">
            🔄 Yeni Tuğrul · Milliyetçi · CHP Geçiş
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_status():
    """Render system status"""
    if st.session_state.agents_initialized:
        st.markdown("""
        <div class="status-indicator">
            <div class="status-dot"></div>
            <span>Sequential Thinking Aktif · 2 Persona Hazır</span>
        </div>
        """, unsafe_allow_html=True)


def format_persona_response(persona_name: str, response: str, is_eski: bool = True) -> str:
    """Format persona response with header"""
    persona_class = "eski" if is_eski else "yeni"
    emoji = "🎯" if is_eski else "🔄"

    return f"""<div class="persona-header-msg {persona_class}">
        {emoji} {persona_name}
    </div>

{response}"""


# Main application
def main():
    """Minimalist main application"""
    init_session_state()

    # Header
    render_header()

    # API key check
    gemini_keys = []
    main_key = os.getenv("GEMINI_API_KEY")
    if main_key:
        gemini_keys.append(main_key)

    for i in range(1, 15):
        key = os.getenv(f"GEMINI_API_KEY_{i}")
        if key:
            gemini_keys.append(key)

    if not gemini_keys:
        st.error("❌ GEMINI API KEY bulunamadı! config/.env dosyasını kontrol edin.")
        st.stop()

    # Status
    render_status()

    # Personas info
    render_personas_info()

    # Agent initialization
    if not st.session_state.agents_initialized:
        with st.spinner("🤖 Persona Agent'lar yükleniyor..."):
            try:
                st.session_state.eski_tugrul_agent = MinimalistPersonaAgent("tugrul_eski")
                st.session_state.yeni_tugrul_agent = MinimalistPersonaAgent("tugrul_yeni")
                st.session_state.agents_initialized = True
                st.success("✅ Agent'lar hazır!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"❌ Agent hatası: {e}")
                st.stop()

    # Display messages directly (no container)
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"], unsafe_allow_html=True)

    # Chat input (moved to after personas)
    if prompt := st.chat_input("💬 İki Tuğrul'a soru sor..."):
        if not st.session_state.processing:
            st.session_state.processing = True

            # Add user message
            user_message = {"role": "user", "content": prompt}
            st.session_state.messages.append(user_message)

            async def process_sequential_responses():
                """Process sequential persona responses"""
                try:
                    # Get responses sequentially
                    eski_response = await st.session_state.eski_tugrul_agent.chat(prompt)
                    yeni_response = await st.session_state.yeni_tugrul_agent.chat(prompt)

                    # Format responses with persona headers
                    eski_formatted = format_persona_response("Eski Tuğrul", eski_response, True)
                    yeni_formatted = format_persona_response("Yeni Tuğrul", yeni_response, False)

                    # Combine responses
                    combined_response = f"{eski_formatted}\n\n---\n\n{yeni_formatted}"

                    # Add assistant message
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": combined_response
                    })

                except Exception as e:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"❌ Sistem hatası: {e}"
                    })
                finally:
                    st.session_state.processing = False

            # Run async
            with st.spinner("🧠 Sequential Thinking..."):
                asyncio.run(process_sequential_responses())
                st.rerun()

    # Control panel
    st.markdown('<div class="control-panel">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🗑️ Temizle"):
            st.session_state.messages = []
            st.session_state.thinking_logs = []
            st.rerun()

    with col2:
        if st.button("🔄 API Değiştir"):
            if st.session_state.agents_initialized:
                st.session_state.eski_tugrul_agent.switch_api_key()
                st.session_state.yeni_tugrul_agent.switch_api_key()
                st.success("🔄 API değiştirildi!")

    with col3:
        if st.button("📊 Durum"):
            st.info(f"""
            **Sistem Durumu**
            - **Gemini Keys:** {len(gemini_keys)} toplam
            - **Smithery API:** {'✅ Aktif' if os.getenv('SMITHERY_API_KEY') else '❌ Kapalı'}
            - **Sequential Mode:** ✅ Aktif
            """)

    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()