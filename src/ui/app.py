#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mini Microcosmos - Streamlit UI (İyileştirilmiş API Rotasyon)
Akıllı API rotasyon sistemi entegre edildi
"""

import json
import os
import asyncio
import sys
import locale
import html
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

# Environment değişkenlerini yükle
load_dotenv(dotenv_path='config/.env')

# Streamlit page config
st.set_page_config(
    page_title="Mini-Microcosmos",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS (önceki CSS kodunuz aynı kalacak)
st.markdown("""
<style>
    /* Önceki CSS kodlarınız burada... */
    .stApp {
        background-color: #0e1117 !important;
        color: #fafafa !important;
        margin: 0 !important;
        padding: 0 !important;
        top: 0 !important;
    }

    /* API Status Bar */
    .api-status-bar {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 8px 15px !important;
        border-radius: 10px !important;
        margin: 0 0 1rem 0 !important;
        text-align: center !important;
        border: 1px solid #333 !important;
        font-size: 0.9rem !important;
    }

    .api-healthy { color: #00ff88 !important; }
    .api-warning { color: #ffaa00 !important; }
    .api-error { color: #ff4444 !important; }

    /* Diğer CSS kodlarınız... */
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
        "agents_initialized": False,
        "api_status": {}
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


class EnhancedPersonaAgent:
    def __init__(self, persona_name="tugrul_eski", log_container=None):
        """Gelişmiş API rotasyon sistemi ile persona agent"""
        setup_encoding()

        self.persona_name = persona_name
        self.log_container = log_container

        # API key yönetimi
        self.api_keys = self._load_gemini_keys()
        self.current_api_index = 0
        self.api_stats = {}
        self.failed_apis = set()
        self.last_api_switch = 0

        # Her API için istatistik başlat
        for i, key in enumerate(self.api_keys):
            self.api_stats[i] = {
                'success_count': 0,
                'error_count': 0,
                'last_success': None,
                'last_error': None,
                'consecutive_errors': 0,
                'is_blocked': False
            }

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

    def _load_gemini_keys(self) -> List[str]:
        """Tüm Gemini API key'lerini yükle"""
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

        # Key'leri karıştır (load balancing için)
        random.shuffle(api_keys)

        return api_keys

    def log(self, message: str, type: str = "info"):
        """Gelişmiş log sistemi"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}][{self.persona_name.upper()}] {message}"
        print(log_message)

        if self.log_container:
            color = {
                "info": "#ccc",
                "success": "#00ff88",
                "warning": "#ffaa00",
                "error": "#ff4444",
                "debug": "#888",
                "api": "#00d4ff"
            }.get(type, "#ccc")

            log_key = f"{self.persona_name}_logs"
            if log_key in st.session_state:
                st.session_state[log_key].append(
                    f"<span style=\"color: {color};\">[{timestamp}] {message}</span>"
                )

    def _initialize_model(self):
        """Gemini modelini başlat"""
        try:
            genai.configure(api_key=self.api_keys[self.current_api_index])
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.log(f"🤖 Model API #{self.current_api_index + 1} ile başlatıldı", "api")
        except Exception as e:
            self.log(f"❌ Model başlatma hatası: {e}", "error")
            raise

    def get_api_health_report(self) -> Dict:
        """API'lerin sağlık durumu raporu"""
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
        stats['last_success'] = time.time()
        stats['consecutive_errors'] = 0
        stats['is_blocked'] = False

    def mark_api_error(self, api_index: int, error: str):
        """API hatasını işaretle"""
        stats = self.api_stats[api_index]
        stats['error_count'] += 1
        stats['last_error'] = time.time()
        stats['consecutive_errors'] += 1

        # 3 ardışık hata sonrası API'yi geçici olarak blokla
        if stats['consecutive_errors'] >= 3:
            stats['is_blocked'] = True
            self.log(f"🚫 API #{api_index + 1} geçici olarak bloklandı", "warning")

    def get_best_api_index(self) -> Optional[int]:
        """En iyi API'yi seç"""
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
            # Tüm API'lar bloklandıysa, blokları kaldır
            self.log("🔄 Tüm API blokları temizleniyor", "warning")
            for stats in self.api_stats.values():
                stats['is_blocked'] = False
                stats['consecutive_errors'] = 0
            return 0

        # En iyi success rate'e sahip API'yi seç
        best_api = max(available_apis, key=lambda x: (x['success_rate'], -x['consecutive_errors']))
        return best_api['index']

    def switch_to_best_api(self):
        """En iyi API'ye geç"""
        old_index = self.current_api_index
        new_index = self.get_best_api_index()

        if new_index is not None and new_index != old_index:
            self.current_api_index = new_index
            self._initialize_model()
            self.last_api_switch = time.time()
            self.log(f"🔄 API #{old_index + 1} → #{new_index + 1}", "api")

        return new_index

    async def try_with_smart_rotation(self, prompt: str, max_retries: Optional[int] = None) -> str:
        """Akıllı API rotasyon ile deneme"""
        if max_retries is None:
            max_retries = len(self.api_keys) * 2

        attempted_apis = set()

        for attempt in range(max_retries):
            current_api = self.current_api_index

            try:
                self.log(f"🧠 API #{current_api + 1} ile deneniyor (Deneme {attempt + 1})", "debug")

                response = await self.model.generate_content_async(prompt)

                # Başarı durumunu kaydet
                self.mark_api_success(current_api)
                result = response.text.strip()

                self.log(f"✅ API #{current_api + 1} başarılı", "success")

                # Session state'e API durumunu kaydet
                if 'api_status' in st.session_state:
                    st.session_state.api_status[self.persona_name] = self.get_api_health_report()

                return result

            except Exception as e:
                error_str = str(e)
                self.log(f"❌ API #{current_api + 1} hatası: {error_str[:100]}", "error")

                # Hata türünü analiz et
                is_quota_error = any(keyword in error_str.lower() for keyword in [
                    "429", "quota", "rate limit", "too many requests", "resource exhausted"
                ])

                is_auth_error = any(keyword in error_str.lower() for keyword in [
                    "401", "403", "invalid api key", "unauthorized", "forbidden"
                ])

                # Hata durumunu kaydet
                self.mark_api_error(current_api, error_str)
                attempted_apis.add(current_api)

                # API durumunu session state'e kaydet
                if 'api_status' in st.session_state:
                    st.session_state.api_status[self.persona_name] = self.get_api_health_report()

                # Eğer quota hatası ise hemen diğer API'ye geç
                if is_quota_error:
                    self.log(f"🚫 API #{current_api + 1} quota aşıldı", "warning")
                    next_api = self.switch_to_best_api()

                    if next_api is None or next_api in attempted_apis:
                        if attempt == max_retries - 1:
                            break
                        continue

                # Auth hatası ise bu API'yi tamamen blokla
                elif is_auth_error:
                    self.log(f"🔒 API #{current_api + 1} auth hatası - bloklanıyor", "error")
                    self.api_stats[current_api]['is_blocked'] = True
                    self.switch_to_best_api()

                # Son deneme mi?
                if attempt == max_retries - 1:
                    break

                # Kısa bekle
                await asyncio.sleep(0.5)

                # Eğer bu API daha önce denenmemişse tekrar dene
                if current_api not in attempted_apis:
                    continue

                # Yeni API'ye geç
                self.switch_to_best_api()

        # Tüm denemeler başarısız
        health_report = self.get_api_health_report()
        self.log(f"💥 Tüm API denemesi başarısız", "error")

        return "Sistem yoğunluğu nedeniyle geçici olarak hizmet veremiyorum. Lütfen biraz sonra tekrar deneyin."

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

    async def sequential_think(self, prompt: str, stage_name: str) -> str:
        """Akıllı API rotasyon ile Sequential Thinking"""
        self.log(f"🧠 {stage_name}")

        thinking_prompt = f"""Sen {self.persona['name']}'sin. Kısa düşün:

{prompt}

2-3 cümleyle düşünceni söyle:"""

        try:
            result = await self.try_with_smart_rotation(thinking_prompt)
            self.log(f"💭 {stage_name}: {result[:100]}...", "debug")
            return result
        except Exception as e:
            self.log(f"❌ {stage_name} kritik hatası: {e}", "error")
            return "Normal yaklaşım benimserim."

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

                    result = await session.call_tool("web_search_exa", {
                        "query": keywords,
                        "num_results": 5
                    })

                    if result.content and len(result.content) > 0:
                        search_result = result.content[0].text[:2000]
                        self.log(f"✅ Arama tamamlandı")

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

    async def chat(self, user_input: str) -> str:
        """Gelişmiş API rotasyon ile sohbet"""
        self.log(f"📝 Soru: {user_input[:50]}...")

        # API sağlık durumu kontrol et
        health_report = self.get_api_health_report()
        self.log(f"📊 API Durumu: {health_report['healthy_apis']}/{health_report['total_apis']} aktif", "api")

        # Sequential thinking ile düşünme süreci
        question_analysis = await self.sequential_think(
            f"'{user_input}' sorusuna nasıl yaklaşmalıyım?",
            "SORU ANALİZİ"
        )

        search_decision = await self.sequential_think(
            f"'{user_input}' için web araması gerekli mi?",
            "ARAMA KARARI"
        )

        # Arama gerekli mi kontrol et
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

            # Web araması (varsa)
            if self.smithery_api_key:
                search_data = await self.search_web_detailed(search_terms.strip())
                analysis = search_data.get("analysis", "")
                news_summary = search_data.get("news_summary", "")

        # Final cevap hazırlama
        self.log("💬 Cevap hazırlanıyor")

        final_prompt = f"""{self.create_system_prompt()}

GÜNCEL BİLGİ:
{news_summary[:800] if news_summary else "Yok"}

ANALİZ:
{analysis[:500] if analysis else ""}

Kullanıcı: "{user_input}"

Kısa ve karakter uygun cevap ver:"""

        try:
            response_text = await self.try_with_smart_rotation(final_prompt)
            self.log("✅ Cevap hazır")

            # Konuşma geçmişine ekle
            self.conversation_history.append({
                'user': user_input,
                'assistant': response_text
            })

            # Son 2 konuşma tut
            if len(self.conversation_history) > 2:
                self.conversation_history = self.conversation_history[-2:]

            return response_text

        except Exception as e:
            self.log(f"❌ Chat kritik hatası: {e}", "error")
            return "Şu anda teknik sorun yaşıyorum, özür dilerim."


# Agent cache
@st.cache_resource
def get_cached_agent(persona_name):
    """Agent'ı cache'le"""
    return EnhancedPersonaAgent(persona_name=persona_name, log_container=True)


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


def display_api_status():
    """API durumunu görüntüle"""
    if 'api_status' in st.session_state and st.session_state.api_status:
        col1, col2 = st.columns(2)

        for i, (persona_name, status) in enumerate(st.session_state.api_status.items()):
            with col1 if i == 0 else col2:
                status_class = {
                    "healthy": "api-healthy",
                    "warning": "api-warning",
                    "critical": "api-error"
                }.get(status["status"], "api-healthy")

                success_rate_percent = int(status["success_rate"] * 100)

                st.markdown(f'''
                <div class="api-status-bar">
                    <strong>{persona_name.upper()}</strong><br>
                    <span class="{status_class}">
                        API: {status["healthy_apis"]}/{status["total_apis"]} aktif 
                        | Başarı: %{success_rate_percent}
                        | Aktif: #{status["current_api"]}
                    </span>
                </div>
                ''', unsafe_allow_html=True)


# Ana uygulama
def main():
    """Ana uygulama"""
    init_session_state()

    # Ana başlık
    st.markdown('''
    <div class="custom-header">
        <h1>🎭 Mini-Microcosmos</h1>
        <p>AI Persona Simulator - Enhanced API Rotation System</p>
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
            <span class="status-success">✅ {len(gemini_keys)} Gemini API Key yüklendi</span>
        </div>
        ''', unsafe_allow_html=True)

    # Agent initialization
    if not st.session_state.agents_initialized:
        with st.spinner("🤖 Enhanced Agent'lar yükleniyor..."):
            try:
                st.session_state.tugrul_agent = get_cached_agent("tugrul_eski")
                st.session_state.yeni_tugrul_agent = get_cached_agent("tugrul_yeni")
                st.session_state.agents_initialized = True
                st.success("✅ Enhanced Agent'lar hazır!")
            except Exception as e:
                st.error(f"❌ Agent hatası: {e}")
                st.stop()

    # API Status Display
    display_api_status()

    # İki sütun
    col1, col2 = st.columns(2)

    # Sol sütun - Eski Tuğrul
    with col1:
        st.markdown('''
        <div class="persona-card">
            <div class="persona-name">🎯 Eski Tuğrul</div>
            <div class="persona-stats">
                <span>Eski Milliyetçi Persona</span>
                <span>Smart API Rotation</span>
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
                <span>Smart API Rotation</span>
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
            with st.spinner("🧠 Enhanced Sequential Thinking..."):
                asyncio.run(process_agents())
                st.rerun()

    # Control panel
    st.markdown("<hr>", unsafe_allow_html=True)
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
        if st.button("📊 API Durumu"):
            if st.session_state.agents_initialized:
                tugrul_status = st.session_state.tugrul_agent.get_api_health_report()
                yeni_tugrul_status = st.session_state.yeni_tugrul_agent.get_api_health_report()

                st.info(f"""
                **Eski Tuğrul:** {tugrul_status['healthy_apis']}/{tugrul_status['total_apis']} API aktif
                **Yeni Tuğrul:** {yeni_tugrul_status['healthy_apis']}/{yeni_tugrul_status['total_apis']} API aktif
                """)

    # Footer
    st.markdown('<p class="footer-text"><strong>🎭 Mini Microcosmos</strong> - Enhanced API Rotation System 🚀</p>',
                unsafe_allow_html=True)


if __name__ == "__main__":
    main()