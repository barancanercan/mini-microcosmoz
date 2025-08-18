#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mini Microcosmos - Modern Minimalist Design
Mobil öncelikli, responsive chat arayüzü - Güncellenmiş versiyon
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

# Modern page config
st.set_page_config(
    page_title="Mini-Microcosmos",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern CSS - Custom Properties tabanlı, minimalist tasarım
st.markdown("""
<style>
/* CSS Custom Properties */
:root {
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --bg-tertiary: #334155;
  --bg-accent: rgba(30, 41, 59, 0.5);

  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;

  --accent-primary: #6366f1;
  --accent-secondary: #8b5cf6;
  --accent-tertiary: #ec4899;

  --success: #22c55e;
  --warning: #f59e0b;
  --error: #ef4444;

  --border-color: #334155;
  --border-light: #475569;

  --radius-lg: 0.75rem;
  --radius-xl: 1rem;
  --radius-full: 9999px;

  --space-sm: 0.5rem;
  --space-md: 0.75rem;
  --space-lg: 1rem;
  --space-xl: 1.5rem;

  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  --shadow-accent: 0 10px 25px -5px rgba(99, 102, 241, 0.25);

  --transition-base: 0.2s ease;
}

/* Reset ve base */
*, *::before, *::after { box-sizing: border-box; }

/* Streamlit UI gizle */
#MainMenu, footer, .stActionButton, header[data-testid="stHeader"] {
  visibility: hidden !important;
  display: none !important;
}

/* App container */
.stApp {
  background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
  color: var(--text-primary);
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
}

/* Ana container */
.main .block-container {
  padding: var(--space-lg) !important;
  max-width: 100% !important;
  width: 100% !important;
}

/* Header */
.app-header {
  text-align: center;
  padding: var(--space-xl) 0;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: var(--space-xl);
}

.app-title {
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary), var(--accent-tertiary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
  letter-spacing: -0.02em;
}

.app-subtitle {
  color: var(--text-secondary);
  font-size: 0.875rem;
  margin: var(--space-sm) 0 0 0;
  font-weight: 400;
}

/* Status bar */
.status-bar {
  background: var(--bg-accent);
  backdrop-filter: blur(16px);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: var(--space-md) var(--space-lg);
  margin-bottom: var(--space-lg);
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.875rem;
  transition: all var(--transition-base);
}

.status-healthy { color: var(--success); }
.status-warning { color: var(--warning); }
.status-error { color: var(--error); }

/* Chat bölümleri */
.chat-section {
  background: var(--bg-accent);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  overflow: hidden;
  height: 70vh;
  display: flex;
  flex-direction: column;
  backdrop-filter: blur(10px);
  transition: all var(--transition-base);
}

.chat-section:hover {
  border-color: var(--border-light);
  box-shadow: var(--shadow-lg);
}

/* Persona header */
.persona-header {
  background: linear-gradient(135deg, var(--bg-secondary), var(--bg-tertiary));
  padding: var(--space-lg);
  border-bottom: 1px solid var(--border-light);
  text-align: center;
  position: relative;
}

.persona-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 50px;
  height: 2px;
  background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
  border-radius: var(--radius-full);
}

.persona-name {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.persona-status {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin: 0.25rem 0 0 0;
  font-weight: 400;
}

/* Chat mesajları için native Streamlit elementleri */
div[data-testid="stChatMessage"] {
  margin-bottom: var(--space-lg) !important;
  opacity: 0;
  animation: messageSlide 0.3s ease forwards;
}

@keyframes messageSlide {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Kullanıcı mesajları */
div[data-testid="stChatMessage"][data-testid*="user"] {
  flex-direction: row-reverse !important;
}

/* Mesaj balonu */
div[data-testid="stChatMessage"] > div {
  background: var(--bg-accent) !important;
  border: 1px solid var(--border-light) !important;
  border-radius: var(--radius-xl) !important;
  padding: 0.875rem 1rem !important;
  max-width: 85% !important;
  box-shadow: var(--shadow-md) !important;
  transition: all var(--transition-base) !important;
  backdrop-filter: blur(8px) !important;
}

/* Kullanıcı mesaj balonu */
div[data-testid="stChatMessage"][data-testid*="user"] > div {
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)) !important;
  color: white !important;
  border: none !important;
}

/* Chat input */
div[data-testid="stChatInput"] > div {
  background: var(--bg-accent) !important;
  border: 1px solid var(--border-light) !important;
  border-radius: var(--radius-full) !important;
  backdrop-filter: blur(16px) !important;
  transition: all var(--transition-base) !important;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
}

div[data-testid="stChatInput"] > div:focus-within {
  border-color: var(--accent-primary) !important;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
}

div[data-testid="stChatInput"] input {
  background: transparent !important;
  color: var(--text-primary) !important;
  border: none !important;
  font-size: 0.875rem !important;
}

div[data-testid="stChatInput"] input::placeholder {
  color: var(--text-secondary) !important;
}

/* Butonlar */
.stButton > button {
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)) !important;
  color: white !important;
  border: none !important;
  border-radius: var(--radius-lg) !important;
  font-weight: 500 !important;
  padding: 0.5rem 1rem !important;
  transition: all var(--transition-base) !important;
  font-size: 0.875rem !important;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
}

.stButton > button:hover {
  transform: translateY(-1px) !important;
  box-shadow: var(--shadow-accent) !important;
}

/* Expander */
.streamlit-expanderHeader {
  background: var(--bg-accent) !important;
  border: 1px solid var(--border-light) !important;
  border-radius: var(--radius-lg) !important;
  color: var(--text-primary) !important;
  font-size: 0.875rem !important;
  transition: all var(--transition-base) !important;
  backdrop-filter: blur(8px) !important;
}

.streamlit-expanderContent {
  background: var(--bg-primary) !important;
  border: 1px solid var(--border-color) !important;
  border-top: none !important;
  border-radius: 0 0 var(--radius-lg) var(--radius-lg) !important;
  padding: var(--space-md) !important;
  font-size: 0.75rem !important;
  max-height: 200px !important;
  overflow-y: auto !important;
}

/* Alert styling */
.stSuccess {
  background: rgba(34, 197, 94, 0.1) !important;
  border: 1px solid var(--success) !important;
  border-radius: var(--radius-lg) !important;
  color: var(--success) !important;
}

.stError {
  background: rgba(239, 68, 68, 0.1) !important;
  border: 1px solid var(--error) !important;
  border-radius: var(--radius-lg) !important;
  color: var(--error) !important;
}

.stInfo {
  background: rgba(99, 102, 241, 0.1) !important;
  border: 1px solid var(--accent-primary) !important;
  border-radius: var(--radius-lg) !important;
  color: var(--accent-primary) !important;
}

/* Footer */
.app-footer {
  text-align: center;
  color: var(--text-muted);
  font-size: 0.75rem;
  margin-top: 2rem;
  padding: var(--space-lg);
  border-top: 1px solid var(--border-color);
}

/* Mobile */
@media (max-width: 768px) {
  .main .block-container {
    padding: 0.75rem !important;
  }

  .app-title {
    font-size: 1.5rem;
  }

  .chat-section {
    height: 60vh;
  }

  .persona-header {
    padding: 0.75rem;
  }

  div[data-testid="stChatMessage"] > div {
    max-width: 90% !important;
    padding: 0.75rem !important;
  }

  .status-bar {
    padding: 0.5rem 0.75rem;
    font-size: 0.8rem;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }

  .stButton > button {
    width: 100% !important;
    margin-bottom: 0.5rem !important;
  }
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
""", unsafe_allow_html=True)


# Mevcut Enhanced Agent sınıfınızı burada kullanın (kısaltılmış versiyon)
class EnhancedPersonaAgent:
    def __init__(self, persona_name="tugrul_eski", log_container=None):
        self.persona_name = persona_name
        self.log_container = log_container

        # API key yönetimi
        self.api_keys = self._load_gemini_keys()
        self.current_api_index = 0
        self.api_stats = {}
        self.failed_apis = set()

        # API stats başlat
        for i, key in enumerate(self.api_keys):
            self.api_stats[i] = {
                'success_count': 0,
                'error_count': 0,
                'consecutive_errors': 0,
                'is_blocked': False
            }

        # Smithery API
        self.smithery_api_key = os.getenv("SMITHERY_API_KEY")
        self.smithery_profile = os.getenv("SMITHERY_PROFILE")

        # Model başlat
        self._initialize_model()

        # Persona yükle
        self.persona = self._load_persona(persona_name)
        self.conversation_history = []

    def _load_gemini_keys(self) -> List[str]:
        """Gemini API keylerini yükle"""
        api_keys = []

        main_key = os.getenv("GEMINI_API_KEY")
        if main_key:
            api_keys.append(main_key)

        for i in range(1, 17):
            key = os.getenv(f"GEMINI_API_KEY_{i}")
            if key:
                api_keys.append(key)

        if not api_keys:
            raise ValueError("❌ Hiçbir GEMINI API key bulunamadı!")

        random.shuffle(api_keys)
        return api_keys

    def _initialize_model(self):
        """Gemini modelini başlat"""
        try:
            genai.configure(api_key=self.api_keys[self.current_api_index])
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            raise Exception(f"Model başlatma hatası: {e}")

    def _load_persona(self, persona_name):
        """Persona yükle"""
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

    def log(self, message: str, type: str = "info"):
        """Log sistemi"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"

        if self.log_container:
            color = {
                "info": "#94a3b8",
                "success": "#22c55e",
                "warning": "#f59e0b",
                "error": "#ef4444",
                "api": "#6366f1"
            }.get(type, "#94a3b8")

            log_key = f"{self.persona_name}_logs"
            if log_key in st.session_state:
                st.session_state[log_key].append(
                    f'<span style="color: {color};">{log_message}</span>'
                )

    def get_api_health_report(self) -> Dict:
        """API sağlık raporu"""
        healthy_apis = sum(1 for stats in self.api_stats.values() if not stats['is_blocked'])
        total_apis = len(self.api_keys)

        total_success = sum(stats['success_count'] for stats in self.api_stats.values())
        total_errors = sum(stats['error_count'] for stats in self.api_stats.values())
        success_rate = total_success / max(total_success + total_errors, 1)

        status = "healthy"
        if healthy_apis < total_apis * 0.3:
            status = "critical"
        elif healthy_apis < total_apis * 0.7:
            status = "warning"

        return {
            "healthy_apis": healthy_apis,
            "total_apis": total_apis,
            "success_rate": success_rate,
            "status": status,
            "current_api": self.current_api_index + 1
        }

    def mark_api_success(self, api_index: int):
        """API başarısını işaretle"""
        stats = self.api_stats[api_index]
        stats['success_count'] += 1
        stats['consecutive_errors'] = 0
        stats['is_blocked'] = False

    def mark_api_error(self, api_index: int, error: str):
        """API hatasını işaretle"""
        stats = self.api_stats[api_index]
        stats['error_count'] += 1
        stats['consecutive_errors'] += 1

        if stats['consecutive_errors'] >= 3:
            stats['is_blocked'] = True
            self.log(f"🚫 API #{api_index + 1} geçici bloklandı", "warning")

    def switch_to_best_api(self):
        """En iyi API'ye geç"""
        available_apis = []

        for i, stats in self.api_stats.items():
            if not stats['is_blocked']:
                total_requests = stats['success_count'] + stats['error_count']
                success_rate = stats['success_count'] / max(total_requests, 1)
                available_apis.append({
                    'index': i,
                    'success_rate': success_rate,
                    'consecutive_errors': stats['consecutive_errors']
                })

        if not available_apis:
            # Tüm API'lar bloklandıysa temizle
            for stats in self.api_stats.values():
                stats['is_blocked'] = False
                stats['consecutive_errors'] = 0
            return 0

        best_api = max(available_apis, key=lambda x: (x['success_rate'], -x['consecutive_errors']))
        old_index = self.current_api_index
        self.current_api_index = best_api['index']

        if old_index != self.current_api_index:
            self._initialize_model()
            self.log(f"🔄 API #{old_index + 1} → #{self.current_api_index + 1}", "api")

        return self.current_api_index

    async def try_with_smart_rotation(self, prompt: str, max_retries: Optional[int] = None) -> str:
        """Akıllı API rotasyon"""
        if max_retries is None:
            max_retries = len(self.api_keys) * 2

        attempted_apis = set()

        for attempt in range(max_retries):
            current_api = self.current_api_index

            try:
                response = await self.model.generate_content_async(prompt)
                self.mark_api_success(current_api)
                result = response.text.strip()
                return result

            except Exception as e:
                error_str = str(e)
                self.log(f"❌ API #{current_api + 1}: {error_str[:50]}...", "error")

                is_quota_error = any(keyword in error_str.lower() for keyword in [
                    "429", "quota", "rate limit", "resource exhausted"
                ])

                self.mark_api_error(current_api, error_str)
                attempted_apis.add(current_api)

                if is_quota_error:
                    self.log(f"🚫 API #{current_api + 1} quota aşıldı", "warning")
                    self.switch_to_best_api()

                if attempt == max_retries - 1:
                    break

                await asyncio.sleep(0.5)

                if current_api not in attempted_apis:
                    continue

                self.switch_to_best_api()

        return "Sistem yoğunluğu nedeniyle geçici olarak hizmet veremiyorum."

    def create_system_prompt(self):
        """Sistem promptu oluştur"""
        bio_text = "\n- ".join(self.persona.get("bio", ["Bilinmiyor"]))
        style_text = "\n- ".join(self.persona.get("style", {}).get("chat", ["Normal konuşur"]))
        lore_text = "\n- ".join(self.persona.get("lore", [""])[:10])

        return f"""Sen {self.persona["name"]}'sin.

BİOGRAFİ:
- {bio_text}

KONUŞMA TARZI:
- {style_text}

HAYATA BAKIŞ:
- {lore_text}

KURALLAR:
- Karakterine uygun davran
- Kısa ve öz cevap ver
- Samimi ve gerçekçi ol"""

    async def sequential_think(self, prompt: str, stage_name: str) -> str:
        """Sequential thinking"""
        self.log(f"🧠 {stage_name}")

        thinking_prompt = f"""Sen {self.persona['name']}'sin. Kısa düşün:

{prompt}

2-3 cümleyle düşünceni söyle:"""

        try:
            result = await self.try_with_smart_rotation(thinking_prompt)
            self.log(f"💭 {stage_name}: {result[:80]}...", "info")
            return result
        except Exception as e:
            self.log(f"❌ {stage_name} hatası: {e}", "error")
            return "Normal yaklaşım benimserim."

    async def search_web_detailed(self, keywords: str):
        """Web araması"""
        if not self.smithery_api_key:
            self.log("❌ Web arama kapalı", "warning")
            return {"analysis": "", "news_summary": ""}

        self.log(f"🔍 Web araması: {keywords[:50]}...")

        try:
            exa_url = f"https://server.smithery.ai/exa/mcp?api_key={self.smithery_api_key}&profile={self.smithery_profile}"

            async with streamablehttp_client(exa_url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()

                    result = await session.call_tool("web_search_exa", {
                        "query": keywords,
                        "num_results": 5
                    })

                    if result.content and len(result.content) > 0:
                        search_result = result.content[0].text[:2000]
                        self.log("✅ Arama tamamlandı", "success")

                        analysis = await self.sequential_think(
                            f"Bu haberleri analiz et: {search_result[:500]}",
                            "ANALİZ"
                        )

                        return {
                            "analysis": analysis,
                            "news_summary": f"Güncel haberler: {search_result[:800]}..."
                        }

            return {"analysis": "", "news_summary": ""}

        except Exception as e:
            self.log(f"❌ Arama hatası: {e}", "error")
            return {"analysis": "", "news_summary": ""}

    async def chat(self, user_input: str) -> str:
        """Ana sohbet fonksiyonu"""
        self.log(f"📝 Soru: {user_input[:50]}...")

        # Sequential thinking
        question_analysis = await self.sequential_think(
            f"'{user_input}' sorusuna nasıl yaklaşmalıyım?",
            "SORU ANALİZİ"
        )

        # Arama gerekli mi?
        search_triggers = ["son", "güncel", "haber", "gündem", "2024", "2025"]
        needs_search = any(trigger in user_input.lower() for trigger in search_triggers)

        analysis = ""
        news_summary = ""

        if needs_search and self.smithery_api_key:
            self.log("🎯 Web araması yapılıyor", "info")
            search_terms = await self.sequential_think(
                f"'{user_input}' için arama terimleri?",
                "ARAMA TERİMLERİ"
            )

            search_data = await self.search_web_detailed(search_terms.strip())
            analysis = search_data.get("analysis", "")
            news_summary = search_data.get("news_summary", "")

        # Final cevap
        self.log("💬 Cevap hazırlanıyor", "info")

        final_prompt = f"""{self.create_system_prompt()}

GÜNCEL BİLGİ:
{news_summary[:800] if news_summary else "Yok"}

ANALİZ:
{analysis[:500] if analysis else ""}

Kullanıcı: "{user_input}"

Kısa ve karakter uygun cevap ver:"""

        try:
            response_text = await self.try_with_smart_rotation(final_prompt)
            self.log("✅ Cevap hazır", "success")

            # Geçmişe ekle
            self.conversation_history.append({
                'user': user_input,
                'assistant': response_text
            })

            if len(self.conversation_history) > 2:
                self.conversation_history = self.conversation_history[-2:]

            return response_text

        except Exception as e:
            self.log(f"❌ Cevap hatası: {e}", "error")
            return "Şu anda teknik sorun yaşıyorum, özür dilerim."


# Session state initialization
def init_session_state():
    """Session state başlat"""
    defaults = {
        "tugrul_messages": [],
        "yeni_tugrul_messages": [],
        "tugrul_logs": [],
        "yeni_tugrul_logs": [],
        "processing": False,
        "agents_initialized": False,
        "api_status": {}
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


# UI Render Functions
def render_header():
    """Modern header render et"""
    st.markdown("""
    <div class="app-header">
        <h1 class="app-title">🎭 Mini-Microcosmos</h1>
        <p class="app-subtitle">AI Persona Simulator · Enhanced Sequential Thinking</p>
    </div>
    """, unsafe_allow_html=True)


def render_status_bar():
    """API status bar"""
    if 'api_status' in st.session_state and st.session_state.api_status:
        tugrul_status = st.session_state.api_status.get('tugrul_eski', {})
        yeni_status = st.session_state.api_status.get('tugrul_yeni', {})

        if tugrul_status and yeni_status:
            st.markdown(f"""
            <div class="status-bar">
                <span class="status-healthy">●</span>
                <strong>System Status:</strong>
                Eski Tuğrul ({tugrul_status.get('healthy_apis', 0)}/{tugrul_status.get('total_apis', 0)} APIs) ·
                Yeni Tuğrul ({yeni_status.get('healthy_apis', 0)}/{yeni_status.get('total_apis', 0)} APIs)
            </div>
            """, unsafe_allow_html=True)


def render_persona_section(persona_title, persona_desc, messages_key, logs_key):
    """Persona bölümü render et"""
    st.markdown(f"""
    <div class="chat-section">
        <div class="persona-header">
            <div class="persona-name">{persona_title}</div>
            <div class="persona-status">{persona_desc}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Thinking process
    if st.session_state.get(logs_key):
        with st.expander("🧠 Sequential Thinking", expanded=False):
            for log in st.session_state[logs_key][-5:]:
                st.markdown(log, unsafe_allow_html=True)

    # Chat messages - Native Streamlit
    for message in st.session_state.get(messages_key, []):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


# Ana uygulama
def main():
    """Modern ana uygulama"""
    init_session_state()

    # Header
    render_header()

    # API key kontrolü
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

    # Status bar
    render_status_bar()

    # Agent initialization
    if not st.session_state.agents_initialized:
        with st.spinner("🤖 Enhanced Agent'lar yükleniyor..."):
            try:
                st.session_state.tugrul_agent = EnhancedPersonaAgent("tugrul_eski", log_container=True)
                st.session_state.yeni_tugrul_agent = EnhancedPersonaAgent("tugrul_yeni", log_container=True)
                st.session_state.agents_initialized = True
                st.success("✅ Enhanced Agent'lar hazır!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"❌ Agent hatası: {e}")
                st.stop()

    # Chat sections
    col1, col2 = st.columns(2, gap="medium")

    with col1:
        render_persona_section(
            "🎯 Eski Tuğrul",
            "Milliyetçi · Geleneksel Değerler",
            "tugrul_messages",
            "tugrul_logs"
        )

    with col2:
        render_persona_section(
            "🔄 Yeni Tuğrul",
            "Milliyetçi · CHP'ye Geçiş",
            "yeni_tugrul_messages",
            "yeni_tugrul_logs"
        )

    # Chat input
    if prompt := st.chat_input("💬 Her iki Tuğrul'a soru sor..."):
        if not st.session_state.processing:
            st.session_state.processing = True

            # Logları temizle
            st.session_state.tugrul_logs = []
            st.session_state.yeni_tugrul_logs = []

            # Kullanıcı mesajını ekle
            user_message = {"role": "user", "content": prompt}
            st.session_state.tugrul_messages.append(user_message)
            st.session_state.yeni_tugrul_messages.append(user_message)

            async def process_agents():
                """Agent'ları işle"""
                try:
                    # Paralel çalıştır
                    tugrul_task = st.session_state.tugrul_agent.chat(prompt)
                    yeni_tugrul_task = st.session_state.yeni_tugrul_agent.chat(prompt)

                    tugrul_response, yeni_tugrul_response = await asyncio.gather(
                        tugrul_task, yeni_tugrul_task
                    )

                    # Cevapları ekle
                    st.session_state.tugrul_messages.append({
                        "role": "assistant",
                        "content": tugrul_response
                    })
                    st.session_state.yeni_tugrul_messages.append({
                        "role": "assistant",
                        "content": yeni_tugrul_response
                    })

                    # API status güncelle
                    st.session_state.api_status['tugrul_eski'] = st.session_state.tugrul_agent.get_api_health_report()
                    st.session_state.api_status[
                        'tugrul_yeni'] = st.session_state.yeni_tugrul_agent.get_api_health_report()

                except Exception as e:
                    st.error(f"❌ Agent hatası: {e}")
                finally:
                    st.session_state.processing = False

            # Async çalıştır
            with st.spinner("🧠 Enhanced Sequential Thinking..."):
                asyncio.run(process_agents())
                st.rerun()

    # Control panel
    st.markdown("---")
    control_col1, control_col2, control_col3 = st.columns(3)

    with control_col1:
        if st.button("🗑️ Sohbeti Temizle"):
            st.session_state.tugrul_messages = []
            st.session_state.yeni_tugrul_messages = []
            st.session_state.tugrul_logs = []
            st.session_state.yeni_tugrul_logs = []
            st.session_state.api_status = {}
            st.rerun()

    with control_col2:
        if st.button("🔄 API Değiştir"):
            if st.session_state.agents_initialized:
                st.session_state.tugrul_agent.switch_to_best_api()
                st.session_state.yeni_tugrul_agent.switch_to_best_api()
                st.success("🔄 En iyi API'lere geçildi!")

    with control_col3:
        if st.button("📊 System Status"):
            if st.session_state.agents_initialized:
                tugrul_status = st.session_state.tugrul_agent.get_api_health_report()
                yeni_tugrul_status = st.session_state.yeni_tugrul_agent.get_api_health_report()

                st.info(f"""
                **System Health Report**
                - **Eski Tuğrul:** {tugrul_status['healthy_apis']}/{tugrul_status['total_apis']} APIs aktif
                - **Yeni Tuğrul:** {yeni_tugrul_status['healthy_apis']}/{yeni_tugrul_status['total_apis']} APIs aktif
                - **Gemini Keys:** {len(gemini_keys)} toplam
                """)

    # Footer
    st.markdown("""
    <div class="app-footer">
        <strong>🎭 Mini-Microcosmos</strong> · 
        Modern AI Persona Simulator · Sequential Thinking Architecture 🧠
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()