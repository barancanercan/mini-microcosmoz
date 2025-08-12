#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mini Microcosmos - Streamlit UI with main.py Architecture
Sequential Thinking mimarisi ile güvenli ve yapılandırılmış persona simülasyonu
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


# CSS yükle
def load_css():
    try:
        with open('static/css/style.css', 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("CSS dosyası bulunamadı: static/css/style.css")


# Streamlit page config
st.set_page_config(
    page_title="Mini Microcosmos - AI Persona Simulator",
    page_icon="🎭",
    layout="wide"
)

# CSS yükle
load_css()


# Encoding yapılandırması
def setup_encoding():
    """Sistem encoding'ini güvenli şekilde yapılandır"""
    try:
        locale.setlocale(locale.LC_ALL, 'tr_TR.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'C.UTF-8')
        except:
            pass

    # Stdin/stdout encoding
    if hasattr(sys.stdin, 'reconfigure'):
        try:
            sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
            sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
            sys.stderr.reconfigure(encoding='utf-8', errors='ignore')
        except:
            pass

    os.environ['PYTHONIOENCODING'] = 'utf-8'


# Session state initialization
def init_session_state():
    """Session state'i güvenli şekilde başlat"""
    defaults = {
        "tugrul_messages": [],
        "yeni_tugrul_messages": [],
        "tugrul_logs": [],
        "yeni_tugrul_logs": [],
        "processing": False,
        "current_stage": "",
        "agents_initialized": False
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


class PersonaAgent:
    def __init__(self, persona_name="tugrul_bey", log_container=None):
        """
        Persona tabanlı AI agent - main.py'den birebir alındı
        """
        setup_encoding()

        self.persona_name = persona_name
        self.log_container = log_container

        # API keys'leri environment'tan al
        self.api_keys = self._load_api_keys()
        self.current_api_index = 0

        # Smithery API yapılandırması
        self.smithery_api_key = os.getenv("SMITHERY_API_KEY")
        self.smithery_profile = os.getenv("SMITHERY_PROFILE")

        if not self.smithery_api_key or not self.smithery_profile:
            self.log("⚠️ SMITHERY API bilgileri .env dosyasında bulunamadı!")
            self.log("💡 Web arama işlevselliği çalışmayabilir")

        # Gemini modelini başlat
        self._initialize_model()

        # Persona'yı yükle
        self.persona = self._load_persona(persona_name)

        # Konuşma geçmişi
        self.conversation_history = []

    def log(self, message, type="info"):
        """Log mesajını konsola ve UI'ya yaz"""
        log_message = f"[{self.persona_name.upper()}][{type.upper()}] {message}"
        print(log_message)

        # UI'da göstermek için
        if self.log_container:
            color = {
                "info": "#495057",
                "success": "#28a745",
                "warning": "#ffc107",
                "error": "#dc3545",
                "debug": "#6c757d"
            }.get(type, "black")

            log_key = f"{self.persona_name}_logs"
            if log_key in st.session_state:
                st.session_state[log_key].append(
                    f"<span style=\"color: {color};\">[{type.upper()}] {message}</span>"
                )

    def _load_api_keys(self):
        """Environment'tan API keys'leri güvenli şekilde yükle"""
        api_keys = []

        # Tek key varsa
        single_key = os.getenv("GEMINI_API_KEY")
        if single_key:
            api_keys.append(single_key)

        # Çoklu key varsa (GEMINI_API_KEY_1, GEMINI_API_KEY_2, ...)
        i = 1
        while True:
            key = os.getenv(f"GEMINI_API_KEY_{i}")
            if key:
                api_keys.append(key)
                i += 1
            else:
                break

        if not api_keys:
            raise ValueError("❌ Hiçbir GEMINI API key bulunamadı! config/.env dosyasını kontrol edin.")

        return api_keys

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
                self.log(f"✅ {persona['name']} persona'sı yüklendi")
                return persona
        except FileNotFoundError:
            self.log(f"❌ src/personas/{persona_name}.json dosyası bulunamadı!")
            return self._get_fallback_persona(persona_name)
        except Exception as e:
            self.log(f"⚠️ Persona yükleme hatası: {e}")
            return self._get_fallback_persona(persona_name)

    def _get_fallback_persona(self, persona_name):
        """Fallback persona"""
        return {
            "name": persona_name.replace('_', ' ').title(),
            "bio": ["Genel bir persona"],
            "style": {"chat": ["Normal konuşur"]},
            "lore": [""],
            "knowledge": [""]
        }

    def switch_api_key(self):
        """API key'i değiştir"""
        self.current_api_index = (self.current_api_index + 1) % len(self.api_keys)
        self._initialize_model()
        self.log(f"🔄 API KEY DEĞİŞTİRİLDİ: #{self.current_api_index + 1}")

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

        return "Sistem yoğunluğu nedeniyle geçici olarak hizmet veremiyorum. Lütfen biraz sonra tekrar deneyin."

    def create_system_prompt(self):
        """Persona'dan sistem promptu oluştur"""
        bio_text = "\n- ".join(self.persona.get("bio", ["Bilinmiyor"]))
        style_text = "\n- ".join(self.persona.get("style", {}).get("chat", ["Normal konuşur"]))
        lore_text = "\n- ".join(self.persona.get("lore", [""])[:15])
        knowledge_text = "\n- ".join(self.persona.get("knowledge", [""])[:8])

        return f"""Sen {self.persona["name"]}'sin. Aşağıdaki kimliğin:

BİOGRAFİ:
- {bio_text}

KONUŞMA TARZI:
- {style_text}

HAYATA BAKIŞ:
- {lore_text}

BİLGİN:
- {knowledge_text}

ÖNEMLİ KURALLAR:
- Karakterine uygun davran
- Güncel olayları web aramalarından öğreniyorsun
- Kendi görüşlerini belirt ama saygılı ol
- Detaylı bilgi ver ama çok uzun olma"""

    async def sequential_think(self, prompt: str, stage_name: str):
        """Sequential Thinking adımı"""
        self.log(f"🧠 {stage_name.upper()} DÜŞÜNÜLÜYOR...")
        st.session_state.current_stage = stage_name

        thinking_prompt = f"""Sen {self.persona['name']}'sin. Aşağıdaki konuyu adım adım düşün:

{prompt}

DÜŞÜNME SÜRECİN:
1. Bu durumu nasıl algılıyorsun?
2. Ne yapman gerekiyor?
3. Kararın nedir?

Kısa ve net düşünceni söyle (2-3 cümle):"""

        try:
            result = await self.try_with_api_rotation(thinking_prompt)
            self.log(f"💭 {stage_name.upper()} SONUCU: {result}")
            return result
        except Exception as e:
            self.log(f"❌ {stage_name} düşünme hatası: {e}")
            fallback_responses = {
                "SORU_ANALIZI": "Normal bir soru, karakterime uygun cevap vereceğim.",
                "ARAMA_KARARI": "Güncel konular için web araması gerekebilir.",
                "ARAMA_TERIMLERI": "Türkiye gündem haberleri",
                "HABER_ANALIZI": "Haberleri kendi perspektifimden değerlendireceğim.",
                "CEVAP_PLANLAMA": "Detaylı ve samimi bir cevap vereceğim."
            }
            result = fallback_responses.get(stage_name, "Normal yaklaşım benimserim")
            self.log(f"💭 {stage_name.upper()} FALLBACK: {result}")
            return result

    def get_current_date(self):
        """Güncel tarihi al"""
        try:
            current_time = datetime.now()
            date_str = current_time.strftime("%d %B %Y, %A")
            self.log(f"📅 BUGÜNÜN TARİHİ: {date_str}")
            return date_str
        except Exception as e:
            self.log(f"⚠️ Tarih alma hatası: {e}")
            fallback_date = "Bilinmeyen Tarih"
            self.log(f"📅 FALLBACK TARİH: {fallback_date}")
            return fallback_date

    async def search_web_detailed(self, keywords: str):
        """Kapsamlı web araması - main.py'den birebir alındı"""
        if not self.smithery_api_key or not self.smithery_profile:
            self.log("❌ Web arama yapılandırması eksik")
            return {
                "raw_results": "",
                "news_summary": "",
                "analysis": "",
                "current_date": self.get_current_date(),
                "sites_count": 0,
                "search_count": 0
            }

        self.log(f"🔍 KAPSAMLI WEB ARAMASI BAŞLANIYOR: '{keywords}'")
        current_date = self.get_current_date()

        exa_url = f"https://server.smithery.ai/exa/mcp?api_key={self.smithery_api_key}&profile={self.smithery_profile}"

        try:
            async with streamablehttp_client(exa_url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()

                    all_results = []

                    # Çoklu arama stratejisi - main.py'deki gibi
                    search_queries = [
                        {"query": keywords, "num_results": 8, "label": "ANA ARAMA"},
                        {"query": "Türkiye haberleri gündem", "num_results": 6, "label": "GÜNCEL HABERLER"},
                        {"query": f"{keywords} ekonomi", "num_results": 5, "label": "EKONOMİ ARAMASI"},
                        {"query": f"{keywords} siyaset politik", "num_results": 5, "label": "SİYASET ARAMASI"},
                    ]

                    self.log(f"🎯 TOPLAM {len(search_queries)} FARKLI ARAMA YAPILACAK")

                    for i, search_config in enumerate(search_queries, 1):
                        try:
                            self.log(f"🔍 {i}. {search_config['label']}: '{search_config['query']}'")

                            search_params = {
                                "query": search_config["query"],
                                "num_results": search_config["num_results"]
                            }

                            result = await session.call_tool("web_search_exa", search_params)

                            if result.content and len(result.content) > 0:
                                all_results.append(result.content[0].text)
                                self.log(f"✅ {i}. ARAMA: {len(result.content[0].text)} karakter")
                            else:
                                self.log(f"⚠️ {i}. ARAMA: Sonuç bulunamadı")

                            await asyncio.sleep(0.2)

                        except Exception as e:
                            self.log(f"❌ {i}. ARAMA HATASI: {e}")
                            continue

                    # Sonuçları birleştir
                    search_result = "\n\n--- ARAMA SONUCU AYIRICI ---\n\n".join(all_results)

                    if search_result:
                        self.log(f"📊 TOPLAM ARAMA SONUCU: {len(search_result)} karakter")

                        # Basit özet (quota'dan korunmak için)
                        news_summary = f"=== GÜNDEM ÖZETİ ===\n{search_result[:1500]}..."

                        analysis = await self.sequential_think(
                            f"Bu güncel bilgileri analiz et: {news_summary[:500]}",
                            "DETAYLI_ANALIZ"
                        )

                        return {
                            "raw_results": search_result[:10000],
                            "news_summary": news_summary,
                            "analysis": analysis,
                            "current_date": current_date,
                            "sites_count": len(all_results),
                            "search_count": len(all_results)
                        }
                    else:
                        self.log("❌ TÜM ARAMALAR BAŞARISIZ")
                        return {
                            "raw_results": "",
                            "news_summary": "",
                            "analysis": "",
                            "current_date": current_date,
                            "sites_count": 0,
                            "search_count": 0
                        }

        except Exception as e:
            self.log(f"❌ Web arama hatası: {e}")
            return {
                "raw_results": "",
                "news_summary": "",
                "analysis": "",
                "current_date": current_date,
                "sites_count": 0,
                "search_count": 0
            }

    async def chat(self, user_input: str):
        """Ana sohbet fonksiyonu - main.py'den birebir alındı"""
        self.log(f"\n{'=' * 60}")
        self.log(f"📝 KULLANICI: {user_input}")
        self.log("=" * 60)

        # Sequential Thinking pipeline
        question_analysis = await self.sequential_think(
            f"Kullanıcı '{user_input}' diyor. Bu soruya nasıl yaklaşmalısın?",
            "SORU_ANALIZI"
        )

        search_decision = await self.sequential_think(
            f"'{user_input}' için web araması gerekli mi? Bu güncel bir konu mu?",
            "ARAMA_KARARI"
        )

        # Arama tetikleyicileri
        search_triggers = [
            "son", "güncel", "yeni", "bugün", "haber", "gündem", "olay",
            "ne oluyor", "neler oldu", "ekonomi", "politika", "seçim",
            "2024", "2025"
        ]

        user_lower = user_input.lower()
        needs_search = any(trigger in user_lower for trigger in search_triggers) or \
                       "arama gerek" in search_decision.lower()

        current_date = self.get_current_date()
        analysis = ""
        news_summary = ""

        if needs_search:
            self.log("🎯 GÜNCEL BİLGİ ARANACAK")

            search_terms = await self.sequential_think(
                f"'{user_input}' için en iyi arama terimleri neler?",
                "ARAMA_TERIMLERI"
            )

            search_data = await self.search_web_detailed(search_terms.strip())
            analysis = search_data["analysis"]
            news_summary = search_data["news_summary"]

            self.log(f"📊 ARAMA ÖZETİ: {search_data['search_count']} arama, {search_data['sites_count']} site")
        else:
            self.log("⚡ GENEL SOHBET")

        # Cevap planlama
        response_plan = await self.sequential_think(
            f"Soru: '{user_input}' | Güncel bilgi: {'Var' if analysis else 'Yok'} | Nasıl cevap vereyim?",
            "CEVAP_PLANLAMA"
        )

        # Final cevap
        self.log("💬 CEVAP HAZIRLANIYOR...")

        # Geçmiş ekle
        history_text = ""
        if self.conversation_history:
            recent = self.conversation_history[-1:]
            for h in recent:
                history_text += f"Önceki: Sen: {h['user'][:100]}... | Ben: {h['assistant'][:100]}...\n"

        final_prompt = f"""{self.create_system_prompt()}

BUGÜNÜN TARİHİ: {current_date}

DÜŞÜNME SÜRECİ:
Soru Analizi: {question_analysis[:300]}
Cevap Planı: {response_plan[:300]}

{"GÜNCEL HABERLER:" if news_summary else ""}
{news_summary[:1500] if news_summary else ""}

{"KİŞİSEL ANALİZ:" if analysis else ""}
{analysis[:1500] if analysis else ""}

{history_text}

Kullanıcı: "{user_input}"

Karakterine uygun, detaylı cevap ver:"""

        try:
            self.log("🤖 CEVAP ÜRETİLİYOR...")
            response_text = await self.try_with_api_rotation(final_prompt)
            self.log(f"✅ CEVAP HAZIR: {len(response_text)} karakter")

            # Geçmişe ekle
            self.conversation_history.append({
                'user': user_input,
                'assistant': response_text
            })

            # Son 3 konuşma tut
            if len(self.conversation_history) > 3:
                self.conversation_history = self.conversation_history[-3:]

            return response_text

        except Exception as e:
            self.log(f"❌ CEVAP ÜRETME HATASI: {e}")
            return "Özür dilerim, şu anda teknik bir sorun yaşıyorum. Lütfen biraz sonra tekrar deneyin."


# Agent cache
@st.cache_resource
def get_cached_agent(persona_name):
    """Agent'ı cache'le"""
    return PersonaAgent(persona_name=persona_name, log_container=True)


# UI Helper Functions
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


def display_thinking_process(logs, container):
    """Düşünce sürecini görüntüle"""
    if logs:
        with container:
            with st.expander("🧠 Sequential Thinking Process", expanded=False):
                for log in logs[-15:]:  # Son 15 log
                    st.markdown(log, unsafe_allow_html=True)


def display_mcp_status():
    """MCP bağlantı durumunu göster"""
    smithery_key = os.getenv("SMITHERY_API_KEY")
    smithery_profile = os.getenv("SMITHERY_PROFILE")

    if smithery_key and smithery_profile:
        st.markdown('<div class="mcp-status mcp-connected">🔗 MCP Connected</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div class="mcp-status mcp-disconnected">❌ MCP Disconnected</div>',
                    unsafe_allow_html=True)


def display_sequential_steps(current_stage):
    """Sequential thinking adımlarını göster"""
    steps = ["SORU_ANALIZI", "ARAMA_KARARI", "ARAMA_TERIMLERI", "HABER_ANALIZI", "CEVAP_PLANLAMA"]

    steps_html = '<div class="sequential-steps">'
    for step in steps:
        if step == current_stage:
            step_class = "step step-active"
        elif steps.index(step) < steps.index(current_stage) if current_stage in steps else False:
            step_class = "step step-completed"
        else:
            step_class = "step step-pending"

        steps_html += f'<div class="{step_class}">{step.replace("_", " ")}</div>'
    steps_html += '</div>'

    st.markdown(steps_html, unsafe_allow_html=True)


# Ana Streamlit Uygulaması
def main():
    """Ana uygulama"""

    # Initialize session state
    init_session_state()

    # Header
    st.markdown("# 🎭 Mini Microcosmos - AI Persona Simulator")
    st.markdown("### 🧠 Sequential Thinking Mimarisi")

    # MCP Status
    display_mcp_status()

    # Agent initialization
    if not st.session_state.agents_initialized:
        with st.spinner("🤖 Agent'lar yükleniyor..."):
            try:
                st.session_state.tugrul_agent = get_cached_agent("tugrul_bey")
                st.session_state.yeni_tugrul_agent = get_cached_agent("yeni_tugrul")
                st.session_state.agents_initialized = True
                st.success("✅ Agent'lar başarıyla yüklendi!")
            except Exception as e:
                st.error(f"❌ Agent yükleme hatası: {e}")
                st.stop()

    # İki sütun ana layout
    col1, col2 = st.columns(2)

    # Sol sütun - Eski Tuğrul
    with col1:
        st.markdown(
            '<div class="persona-card"><div class="persona-name">🎯 Eski Tuğrul</div><div class="persona-stats"><span>MHP/Ülkücü</span><span>Milliyetçi</span></div></div>',
            unsafe_allow_html=True)

        # Thinking process
        thinking_container1 = st.container()
        display_thinking_process(st.session_state.tugrul_logs, thinking_container1)

        # Messages
        message_container1 = st.container()
        display_messages(st.session_state.tugrul_messages, message_container1)

    # Sağ sütun - Yeni Tuğrul  
    with col2:
        st.markdown(
            '<div class="persona-card"><div class="persona-name">🔄 Yeni Tuğrul</div><div class="persona-stats"><span>CHP Geçiş</span><span>Değişen Profil</span></div></div>',
            unsafe_allow_html=True)

        # Thinking process
        thinking_container2 = st.container()
        display_thinking_process(st.session_state.yeni_tugrul_logs, thinking_container2)

        # Messages
        message_container2 = st.container()
        display_messages(st.session_state.yeni_tugrul_messages, message_container2)

    # Sequential steps indicator
    if st.session_state.current_stage:
        st.markdown("---")
        display_sequential_steps(st.session_state.current_stage)

    # Chat input
    st.markdown("---")

    if prompt := st.chat_input("🎭 Tuğrullara bir şey sor..."):
        if not st.session_state.processing:
            st.session_state.processing = True

            # Clear logs for new conversation
            st.session_state.tugrul_logs = []
            st.session_state.yeni_tugrul_logs = []
            st.session_state.current_stage = ""

            # Add user message
            user_message = {"role": "user", "content": prompt}
            st.session_state.tugrul_messages.append(user_message)
            st.session_state.yeni_tugrul_messages.append(user_message)

            # Progress tracking
            progress_container = st.container()

            async def process_agents():
                """Agent'ları async olarak çalıştır"""

                with progress_container:
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    try:
                        # Eski Tuğrul
                        status_text.text("🎯 Eski Tuğrul Sequential Thinking...")
                        progress_bar.progress(25)

                        tugrul_response = await st.session_state.tugrul_agent.chat(prompt)
                        st.session_state.tugrul_messages.append({
                            "role": "assistant",
                            "content": tugrul_response
                        })

                        progress_bar.progress(50)

                        # Yeni Tuğrul
                        status_text.text("🔄 Yeni Tuğrul Sequential Thinking...")
                        progress_bar.progress(75)

                        yeni_tugrul_response = await st.session_state.yeni_tugrul_agent.chat(prompt)
                        st.session_state.yeni_tugrul_messages.append({
                            "role": "assistant",
                            "content": yeni_tugrul_response
                        })

                        progress_bar.progress(100)
                        status_text.text("✅ Sequential Thinking tamamlandı!")

                        # Clean up
                        progress_bar.empty()
                        status_text.empty()

                    except Exception as e:
                        st.error(f"❌ Agent işlem hatası: {e}")

                    finally:
                        st.session_state.processing = False
                        st.session_state.current_stage = ""

            # Run async function
            with st.spinner("🧠 Sequential Thinking Pipeline çalışıyor..."):
                asyncio.run(process_agents())
                st.rerun()

    # Control panel
    st.markdown("---")
    control_col1, control_col2, control_col3, control_col4 = st.columns(4)

    with control_col1:
        if st.button("🗑️ Sohbeti Temizle"):
            st.session_state.tugrul_messages = []
            st.session_state.yeni_tugrul_messages = []
            st.session_state.tugrul_logs = []
            st.session_state.yeni_tugrul_logs = []
            st.session_state.current_stage = ""
            st.rerun()

    with control_col2:
        if st.button("📊 İstatistikler"):
            st.info(f"""
            **📈 Sistem Durumu:**
            - Eski Tuğrul: {len(st.session_state.tugrul_messages)} mesaj
            - Yeni Tuğrul: {len(st.session_state.yeni_tugrul_messages)} mesaj
            - MCP: {"✅ Bağlı" if os.getenv("SMITHERY_API_KEY") else "❌ Bağlı değil"}
            - API Keys: {len(st.session_state.tugrul_agent.api_keys) if st.session_state.agents_initialized else 0}
            """)

    with control_col3:
        if st.button("🔄 API Key Değiştir"):
            if st.session_state.agents_initialized:
                st.session_state.tugrul_agent.switch_api_key()
                st.session_state.yeni_tugrul_agent.switch_api_key()
                st.success("🔄 API Keys değiştirildi!")

    with control_col4:
        if st.button("🔧 Sistem Bilgisi"):
            st.info(f"""
            **🔧 Teknik Detaylar:**
            - Sequential Thinking: ✅ Aktif
            - MCP Protocol: {'✅ Bağlı' if os.getenv("SMITHERY_API_KEY") else '❌ Eksik'}
            - Persona Count: 2
            - Architecture: main.py mirror
            """)

    # Footer
    st.markdown("---")
    st.markdown("**🎭 Mini Microcosmos** - Sequential Thinking ile güvenli AI persona simülasyonu")


if __name__ == "__main__":
    main()