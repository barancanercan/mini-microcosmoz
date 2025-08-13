#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mini Microcosmos - Streamlit UI (Final Düzeltilmiş)
Başlık problemi ve beyaz alan tamamen çözüldü
"""

import json
import os
import asyncio
import sys
import locale
import html
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

import streamlit as st

# Path setup
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Environment değişkenlerini yükle
load_dotenv(dotenv_path='config/.env')

# Streamlit page config - Beyaz boşluk için optimize edilmiş
st.set_page_config(
    page_title="Mini-Microcosmos",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS'i en üste yerleştir - Tüm sorunlar çözüldü
st.markdown("""
<style>
    /* GLOBAL RESET - Her şeyi sıfırla */
    html, body, div, span, h1, h2, h3, p {
        margin: 0 !important;
        padding: 0 !important;
    }

    /* STREAMLIT APP CONTAINER - Ana konteyner */
    .stApp {
        background-color: #0e1117 !important;
        color: #fafafa !important;
        margin: 0 !important;
        padding: 0 !important;
        top: 0 !important;
    }

    /* STREAMLIT HEADER - Tamamen gizle */
    header[data-testid="stHeader"] {
        height: 0px !important;
        display: none !important;
        visibility: hidden !important;
    }

    /* STREAMLIT TOOLBAR - Tamamen gizle */
    .stToolbar {
        display: none !important;
        visibility: hidden !important;
    }

    /* MAIN CONTAINER - Ana içerik alanı */
    .main .block-container {
        padding: 1rem 1rem 0rem 1rem !important;
        margin-top: 0rem !important;
        max-width: 100% !important;
    }

    /* STREAMLIT VIEW CONTAINER */
    section[data-testid="stSidebar"] {
        display: none !important;
    }

    /* BAŞLIK STİLİ - Görünür başlık */
    .main-title {
        background: linear-gradient(135deg, #00d4ff 0%, #667eea 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.5rem !important;
        font-weight: bold !important;
        text-align: center !important;
        margin: 0 0 1rem 0 !important;
        padding: 0 !important;
    }

    /* STATUS BAR */
    .status-bar {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 8px 15px !important;
        border-radius: 10px !important;
        margin: 0 0 1rem 0 !important;
        text-align: center !important;
        border: 1px solid #333 !important;
    }

    /* PERSONA KARTLARI */
    .persona-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%) !important;
        color: #fafafa !important;
        padding: 15px !important;
        border-radius: 15px !important;
        margin: 10px 0 !important;
        text-align: center !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
        border: 1px solid #333 !important;
    }

    .persona-name {
        font-size: 1.3rem !important;
        font-weight: bold !important;
        margin-bottom: 8px !important;
        color: #00d4ff !important;
    }

    .persona-stats {
        display: flex !important;
        justify-content: space-between !important;
        font-size: 0.9rem !important;
        opacity: 0.8 !important;
        color: #ccc !important;
    }

    /* CHAT CONTAINER */
    .chat-container {
        background-color: #1a1a1a !important;
        border-radius: 15px !important;
        padding: 15px !important;
        margin: 10px 0 !important;
        min-height: 400px !important;
        max-height: 500px !important;
        overflow-y: auto !important;
        border: 1px solid #333 !important;
    }

    /* MESAJ BALONLARI */
    .message-bubble {
        padding: 12px 18px !important;
        border-radius: 20px !important;
        margin-bottom: 12px !important;
        max-width: 85% !important;
        word-wrap: break-word !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
        line-height: 1.5 !important;
    }

    .user-bubble {
        background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%) !important;
        color: #000 !important;
        margin-left: 15% !important;
        font-weight: 500 !important;
    }

    .assistant-bubble {
        background: linear-gradient(135deg, #333 0%, #555 100%) !important;
        color: #fafafa !important;
        margin-right: 15% !important;
        border: 1px solid #444 !important;
    }

    /* THINKING PROCESS */
    .streamlit-expanderHeader {
        background-color: #262730 !important;
        color: #fafafa !important;
        border: 1px solid #444 !important;
        border-radius: 10px !important;
        margin: 5px 0 !important;
    }

    .streamlit-expanderContent {
        background-color: #1a1a1a !important;
        color: #ccc !important;
        border: 1px solid #333 !important;
        border-top: none !important;
        border-radius: 0 0 10px 10px !important;
        padding: 10px !important;
    }

    /* CHAT INPUT */
    .stChatInput > div {
        background-color: #262730 !important;
        border-radius: 25px !important;
        border: 1px solid #444 !important;
    }

    .stChatInput input {
        background-color: #262730 !important;
        color: #fafafa !important;
        border: none !important;
        border-radius: 25px !important;
    }

    .stChatInput input::placeholder {
        color: #888 !important;
    }

    /* BUTTONS */
    .stButton > button {
        background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%) !important;
        color: #000 !important;
        border: none !important;
        border-radius: 25px !important;
        font-weight: bold !important;
        padding: 8px 20px !important;
        transition: all 0.3s ease !important;
        margin: 5px 0 !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(0,212,255,0.3) !important;
    }

    /* STATUS INDICATORS */
    .status-success { 
        color: #00ff88 !important; 
        font-weight: bold !important;
    }

    .status-error { 
        color: #ff4444 !important; 
        font-weight: bold !important;
    }

    /* SUCCESS/ERROR MESSAGES */
    .stSuccess {
        background-color: rgba(0, 255, 136, 0.1) !important;
        border: 1px solid #00ff88 !important;
        border-radius: 10px !important;
        color: #00ff88 !important;
    }

    .stError {
        background-color: rgba(255, 68, 68, 0.1) !important;
        border: 1px solid #ff4444 !important;
        border-radius: 10px !important;
        color: #ff4444 !important;
    }

    /* SCROLLBAR */
    ::-webkit-scrollbar {
        width: 8px !important;
    }

    ::-webkit-scrollbar-track {
        background: #1a1a1a !important;
        border-radius: 10px !important;
    }

    ::-webkit-scrollbar-thumb {
        background: #444 !important;
        border-radius: 10px !important;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #666 !important;
    }

    /* DIVIDER */
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, #333, transparent) !important;
        margin: 1rem 0 !important;
    }

    /* FOOTER */
    .footer-text {
        text-align: center !important;
        color: #888 !important;
        font-size: 0.9rem !important;
        margin: 1rem 0 0 0 !important;
        padding: 0 !important;
    }

    /* HIDE STREAMLIT ELEMENTS */
    #MainMenu, footer, .stActionButton {
        display: none !important;
    }

    /* RESPONSIVE DESIGN */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2rem !important;
        }

        .message-bubble {
            max-width: 95% !important;
        }

        .persona-card {
            margin: 5px 0 !important;
            padding: 10px !important;
        }

        .chat-container {
            min-height: 300px !important;
            max-height: 400px !important;
        }
    }
</style>
""", unsafe_allow_html=True)


# Session state initialization
def init_session_state():
    """Session state'i başlat"""
    defaults = {
        "tugrul_messages": [],
        "yeni_tugrul_messages": [],
        "tugrul_logs": [],
        "yeni_tugrul_logs": [],
        "processing": False,
        "agents_initialized": False
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


# Encoding setup
def setup_encoding():
    """Sistem encoding'ini güvenli şekilde yapılandır"""
    try:
        locale.setlocale(locale.LC_ALL, 'tr_TR.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'C.UTF-8')
        except:
            pass

    os.environ['PYTHONIOENCODING'] = 'utf-8'


class PersonaAgent:
    def __init__(self, persona_name="tugrul_eski", log_container=None):
        """Persona tabanlı AI agent"""
        setup_encoding()

        self.persona_name = persona_name
        self.log_container = log_container

        # Çoklu Gemini API keys
        self.api_keys = self._load_gemini_keys()
        self.current_api_index = 0

        # Smithery API
        self.smithery_api_key = os.getenv("SMITHERY_API_KEY")
        self.smithery_profile = os.getenv("SMITHERY_PROFILE")

        if not self.smithery_api_key or not self.smithery_profile:
            self.log("⚠️ Web arama devre dışı")

        # Gemini modelini başlat
        self._initialize_model()

        # Persona'yı yükle
        self.persona = self._load_persona(persona_name)
        self.conversation_history = []

    def _load_gemini_keys(self):
        """Gemini API key'lerini yükle"""
        api_keys = []

        # Ana key
        main_key = os.getenv("GEMINI_API_KEY")
        if main_key:
            api_keys.append(main_key)

        # Numaralı keyler (1-14)
        for i in range(1, 15):
            key = os.getenv(f"GEMINI_API_KEY_{i}")
            if key:
                api_keys.append(key)

        if not api_keys:
            raise ValueError("❌ Hiçbir GEMINI API key bulunamadı!")

        return api_keys

    def log(self, message, type="info"):
        """Log mesajını yaz"""
        log_message = f"[{self.persona_name.upper()}] {message}"
        print(log_message)

        if self.log_container:
            color = {
                "info": "#ccc",
                "success": "#00ff88",
                "warning": "#ffaa00",
                "error": "#ff4444",
                "debug": "#888"
            }.get(type, "#ccc")

            log_key = f"{self.persona_name}_logs"
            if log_key in st.session_state:
                st.session_state[log_key].append(
                    f"<span style=\"color: {color};\">{message}</span>"
                )

    def _initialize_model(self):
        """Gemini modelini başlat"""
        genai.configure(api_key=self.api_keys[self.current_api_index])
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def _load_persona(self, persona_name):
        """Persona JSON dosyasını yükle"""
        try:
            persona_path = f'src/personas/{persona_name}.json'
            with open(persona_path, 'r', encoding='utf-8') as f:
                persona = json.load(f)
                self.log(f"✅ {persona['name']} yüklendi")
                return persona
        except Exception as e:
            self.log(f"❌ Persona hatası: {e}")
            return self._get_fallback_persona(persona_name)

    def _get_fallback_persona(self, persona_name):
        """Fallback persona"""
        return {
            "name": persona_name.replace('_', ' ').title(),
            "bio": ["Test persona"],
            "style": {"chat": ["Normal konuşur"]},
            "lore": [""],
            "knowledge": [""]
        }

    def switch_api_key(self):
        """API key'i değiştir"""
        self.current_api_index = (self.current_api_index + 1) % len(self.api_keys)
        self._initialize_model()
        self.log(f"🔄 API #{self.current_api_index + 1} aktif")

    async def try_with_api_rotation(self, prompt, max_retries=None):
        """API rotasyonu ile güvenli deneme"""
        if max_retries is None:
            max_retries = len(self.api_keys)

        for attempt in range(max_retries):
            try:
                response = await self.model.generate_content_async(prompt)
                return response.text.strip()
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    self.log(f"❌ API #{self.current_api_index + 1} quota aşıldı")
                    if attempt < max_retries - 1:
                        self.switch_api_key()
                        continue
                else:
                    raise e

        return "Sistem yoğunluğu nedeniyle geçici olarak hizmet veremiyorum."

    def create_system_prompt(self):
        """Persona'dan sistem promptu oluştur"""
        bio_text = "\n- ".join(self.persona.get("bio", ["Bilinmiyor"]))
        style_text = "\n- ".join(self.persona.get("style", {}).get("chat", ["Normal konuşur"]))
        lore_text = "\n- ".join(self.persona.get("lore", [""])[:10])
        knowledge_text = "\n- ".join(self.persona.get("knowledge", [""])[:6])

        return f"""Sen {self.persona["name"]}'sin.

BİOGRAFİ:
- {bio_text}

KONUŞMA TARZI:
- {style_text}

HAYATA BAKIŞ:
- {lore_text}

BİLGİN:
- {knowledge_text}

KURALLAR:
- Karakterine uygun davran
- Kısa ve öz cevap ver
- Tartışmacı ve ikna edici ol """

    async def sequential_think(self, prompt: str, stage_name: str):
        """Sequential Thinking adımı"""
        self.log(f"🧠 {stage_name}")

        thinking_prompt = f"""Sen {self.persona['name']}'sin. Kısa düşün:

{prompt}

2-3 cümleyle düşünceni söyle:"""

        try:
            result = await self.try_with_api_rotation(thinking_prompt)
            self.log(f"💭 {stage_name}: {result[:100]}...")
            return result
        except Exception as e:
            self.log(f"❌ {stage_name} hatası: {e}")
            return "Normal yaklaşım benimserim."

    async def search_web_detailed(self, keywords: str):
        """Web araması"""
        if not self.smithery_api_key:
            self.log("❌ Web arama kapalı")
            return {"analysis": "", "news_summary": ""}

        self.log(f"🔍 Web araması: {keywords[:50]}...")

        try:
            exa_url = f"https://server.smithery.ai/exa/mcp?api_key={self.smithery_api_key}&profile={self.smithery_profile}"

            async with streamablehttp_client(exa_url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()

                    # Basit arama
                    result = await session.call_tool("web_search_exa", {
                        "query": keywords,
                        "num_results": 5
                    })

                    if result.content and len(result.content) > 0:
                        search_result = result.content[0].text[:2000]
                        self.log(f"✅ Arama tamamlandı")

                        # Basit analiz
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
            self.log(f"❌ Arama hatası: {e}")
            return {"analysis": "", "news_summary": ""}

    async def chat(self, user_input: str):
        """Ana sohbet fonksiyonu"""
        self.log(f"📝 Soru: {user_input[:50]}...")

        # Sequential thinking
        question_analysis = await self.sequential_think(
            f"'{user_input}' sorusuna nasıl yaklaşmalıyım?",
            "SORU ANALİZİ"
        )

        search_decision = await self.sequential_think(
            f"'{user_input}' için web araması gerekli mi?",
            "ARAMA KARARI"
        )

        # Arama gerekli mi?
        search_triggers = ["son", "güncel", "haber", "gündem", "2024", "2025"]
        needs_search = any(trigger in user_input.lower() for trigger in search_triggers)

        analysis = ""
        news_summary = ""

        if needs_search:
            self.log("🎯 Web araması yapılıyor")
            search_terms = await self.sequential_think(
                f"'{user_input}' için arama terimleri?",
                "ARAMA TERİMLERİ"
            )

            search_data = await self.search_web_detailed(search_terms.strip())
            analysis = search_data["analysis"]
            news_summary = search_data["news_summary"]

        # Final cevap
        self.log("💬 Cevap hazırlanıyor")

        final_prompt = f"""{self.create_system_prompt()}

GÜNCEL BİLGİ:
{news_summary[:800] if news_summary else "Yok"}

ANALİZ:
{analysis[:500] if analysis else ""}

Kullanıcı: "{user_input}"

Kısa ve karakter uygun cevap ver:"""

        try:
            response_text = await self.try_with_api_rotation(final_prompt)
            self.log("✅ Cevap hazır")

            # Geçmişe ekle
            self.conversation_history.append({
                'user': user_input,
                'assistant': response_text
            })

            # Son 2 konuşma tut
            if len(self.conversation_history) > 2:
                self.conversation_history = self.conversation_history[-2:]

            return response_text

        except Exception as e:
            self.log(f"❌ Hata: {e}")
            return "Şu anda teknik sorun yaşıyorum, özür dilerim."


# Agent cache
@st.cache_resource
def get_cached_agent(persona_name):
    """Agent'ı cache'le"""
    return PersonaAgent(persona_name=persona_name, log_container=True)


# UI Functions
def display_messages(messages, container):
    """Mesajları görüntüle"""
    with container:
        for message in messages:
            if message["role"] == "user":
                st.markdown(f'<div class="message-bubble user-bubble">{html.escape(message["content"])}</div>',
                            unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="message-bubble assistant-bubble">{html.escape(message["content"])}</div>',
                            unsafe_allow_html=True)


def display_thinking_process(logs, container, persona_name):
    """Düşünce sürecini görüntüle"""
    if logs:
        with container:
            with st.expander("🧠 Sequential Thinking Process", expanded=False):
                for log in logs[-10:]:  # Son 10 log
                    st.markdown(log, unsafe_allow_html=True)


# Ana uygulama
def main():
    """Ana uygulama"""
    init_session_state()

    # Ana başlık - Ortalanmış ve stilize edilmiş
    st.markdown('''
    <div class="custom-header">
        <h1>🎭 Mini-Microcosmos</h1>
        <p>AI Persona Simulator - Sequential Thinking Architecture</p>
    </div>
    ''', unsafe_allow_html=True)

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
        st.error("❌ GEMINI API KEY bulunamadı!")
        st.info("config/.env dosyasına API keylerini ekleyin")
        st.stop()
    else:
        st.markdown(f'''
        <div class="status-bar">
            <span class="status-success">✅ {len(gemini_keys)} Gemini API Key aktif</span>
        </div>
        ''', unsafe_allow_html=True)

    # Agent initialization
    if not st.session_state.agents_initialized:
        with st.spinner("🤖 Agent'lar yükleniyor..."):
            try:
                st.session_state.tugrul_agent = get_cached_agent("tugrul_eski")
                st.session_state.yeni_tugrul_agent = get_cached_agent("tugrul_yeni")
                st.session_state.agents_initialized = True
                st.success("✅ Agent'lar hazır!")
            except Exception as e:
                st.error(f"❌ Agent hatası: {e}")
                st.stop()

    # İki sütun
    col1, col2 = st.columns(2)

    # Sol sütun - Eski Tuğrul
    with col1:
        st.markdown('''
        <div class="persona-card">
            <div class="persona-name">🎯 Eski Tuğrul</div>
            <div class="persona-stats">
                <span>Eski Milliyetçi Persona</span>
                <span>Milliyetçi</span>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        # Thinking process
        thinking_container1 = st.container()
        display_thinking_process(st.session_state.tugrul_logs, thinking_container1, "tugrul")

        # Messages
        message_container1 = st.container()
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        display_messages(st.session_state.tugrul_messages, message_container1)
        st.markdown('</div>', unsafe_allow_html=True)

    # Sağ sütun - Yeni Tuğrul
    with col2:
        st.markdown('''
        <div class="persona-card">
            <div class="persona-name">🔄 Yeni Tuğrul</div>
            <div class="persona-stats">
                <span>Yeni Milliyetçi - CHP Geçiş</span>
                <span>Değişen Profil</span>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        # Thinking process
        thinking_container2 = st.container()
        display_thinking_process(st.session_state.yeni_tugrul_logs, thinking_container2, "yeni_tugrul")

        # Messages
        message_container2 = st.container()
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        display_messages(st.session_state.yeni_tugrul_messages, message_container2)
        st.markdown('</div>', unsafe_allow_html=True)

    # Chat input
    st.markdown("<hr>", unsafe_allow_html=True)

    if prompt := st.chat_input("🎭 Tuğrullara bir şey sor..."):
        if not st.session_state.processing:
            st.session_state.processing = True

            # Clear logs
            st.session_state.tugrul_logs = []
            st.session_state.yeni_tugrul_logs = []

            # Add user message
            user_message = {"role": "user", "content": prompt}
            st.session_state.tugrul_messages.append(user_message)
            st.session_state.yeni_tugrul_messages.append(user_message)

            async def process_agents():
                """Agent'ları çalıştır"""
                try:
                    # Paralel çalışma
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

                except Exception as e:
                    st.error(f"❌ Agent hatası: {e}")
                finally:
                    st.session_state.processing = False

            # Run async
            with st.spinner("🧠 Sequential Thinking..."):
                asyncio.run(process_agents())
                st.rerun()

    # Control panel
    st.markdown("<hr>", unsafe_allow_html=True)
    control_col1, control_col2 = st.columns(2)

    with control_col1:
        if st.button("🗑️ Sohbeti Temizle"):
            st.session_state.tugrul_messages = []
            st.session_state.yeni_tugrul_messages = []
            st.session_state.tugrul_logs = []
            st.session_state.yeni_tugrul_logs = []
            st.rerun()

    with control_col2:
        if st.button("🔄 API Değiştir"):
            if st.session_state.agents_initialized:
                st.session_state.tugrul_agent.switch_api_key()
                st.session_state.yeni_tugrul_agent.switch_api_key()
                st.success("🔄 API değiştirildi!")

    # Footer
    st.markdown('<p class="footer-text"><strong>🎭 Mini Microcosmos</strong> - AI Persona Simulator - developed by Baran Can Ercan with <3 🎭 </p>',
                unsafe_allow_html=True)


if __name__ == "__main__":
    main()