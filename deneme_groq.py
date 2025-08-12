import streamlit as st
import json
import os
import asyncio
import html
from datetime import datetime
from dotenv import load_dotenv
from groq import AsyncGroq

# --- Genel Yapılandırma ---
st.set_page_config(page_title="Microcosmos Simülatörü (Groq)", layout="wide")
load_dotenv()

# --- Sohbet Geçmişi ve Logları Başlatma ---
if "chat_history_eski" not in st.session_state:
    st.session_state.chat_history_eski = []
if "chat_history_yeni" not in st.session_state:
    st.session_state.chat_history_yeni = []
if "eski_logs" not in st.session_state:
    st.session_state.eski_logs = []
if "yeni_logs" not in st.session_state:
    st.session_state.yeni_logs = []
if "processing_prompt" not in st.session_state:
    st.session_state.processing_prompt = None

# --- Stil Dosyası Yükleme ---
def load_css(file_name):
    try:
        with open(file_name, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Stil dosyası bulunamadı: {file_name}")

load_css("style.css")


# --- PersonaAgent Sınıfı (Değişiklik yok) ---
class PersonaAgent:
    def __init__(self, persona_name="tugrul_bey", ui_log_callback=None):
        self.persona_name = persona_name
        self.log_callback = ui_log_callback
        self.log(f"Agent for {persona_name} başlatılıyor.", "info")
        
        self.groq_api_key = os.getenv("GROQ_API_KEY")

        if not self.groq_api_key:
            self.log("Hiçbir GROQ API key bulunamadı! .env dosyasını kontrol edin.", "error")
            st.stop()
        
        self._initialize_model()
        self.persona = self._load_persona(persona_name)
        self.conversation_history = []

    def log(self, message, type="info"):
        log_message = f"[{self.persona_name.upper()}][{type.upper()}] {message}"
        print(log_message)
        if self.log_callback:
            self.log_callback(message, type)

    def _initialize_model(self):
        self.client = AsyncGroq(api_key=self.groq_api_key)
        self.model_name = 'llama3-70b-8192'

    def _load_persona(self, persona_name):
        filepath = f'personas/{persona_name}.json'
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                persona = json.load(f)
                self.log(f"✅ {persona['name']} persona'sı yüklendi.", "info")
                return persona
        except Exception as e:
            self.log(f"❌ Persona yüklenemedi: {filepath}. Hata: {e}", "error")
            return {"name": "Hatalı Persona", "bio": [], "style": {}, "lore": [], "knowledge": []}

    async def call_groq_api(self, messages, max_retries=3, initial_delay=1):
        for attempt in range(max_retries):
            try:
                self.log(f"Groq API çağrısı denemesi {attempt + 1}/{max_retries}. Model: {self.model_name}", "debug")
                chat_completion = await self.client.chat.completions.create(
                    messages=messages,
                    model=self.model_name,
                    temperature=0.7, 
                    max_tokens=1024,
                )
                self.log("Groq API çağrısı başarılı.", "debug")
                return chat_completion.choices[0].message.content
            except Exception as e:
                error_msg = str(e)
                self.log(f"Groq API çağrısı hatası (Deneme {attempt + 1}): {error_msg}", "error")
                if "429" in error_msg:
                    delay = initial_delay * (2 ** attempt)
                    self.log(f"Kota aşıldı. {delay:.2f} saniye bekleniyor...", "warning")
                    await asyncio.sleep(delay)
                else:
                    raise e
        self.log("Tüm Groq API denemeleri başarısız oldu.", "error")
        raise Exception("Groq API'ye ulaşılamıyor veya tüm denemeler başarısız oldu.")

    def create_system_prompt(self):
        bio_text = "\n- ".join(self.persona.get("bio", ["Bilinmiyor"]))
        style_text = "\n- ".join(self.persona.get("style", {}).get("chat", ["Normal konuşur"]))
        lore_text = "\n- ".join(self.persona.get("lore", [""])[:15])
        knowledge_text = "\n- ".join(self.persona.get("knowledge", [""])[:8])
        return f"""
Sen {self.persona.get("name", "Bilinmeyen Karakter")}'sin. Aşağıdaki kimliğin:

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
        self.log(f"🧠 {stage_name.upper()} DÜŞÜNÜLÜYOR...", "info")
        thinking_prompt = f"'{prompt}' konusunu 2-3 cümleyle düşün: 1. Durum ne? 2. Ne yapmalıyım? 3. Kararım ne?"
        
        messages = [
            {"role": "system", "content": self.create_system_prompt()},
            {"role": "user", "content": thinking_prompt}
        ]

        try:
            result = await self.call_groq_api(messages)
            self.log(f"💭 {stage_name.upper()} SONUCU: {result}", "success")
            return result
        except Exception as e:
            self.log(f"❌ {stage_name} düşünme hatası: {e}", "error")
            return "Normal bir yaklaşımla cevap vereceğim."

    async def chat(self, user_input: str):
        self.log(f"💬 Yeni mesaj alındı: '{user_input}'", "info")
        self.conversation_history.append({"role": "user", "content": user_input})

        self.log("--- Düşünce Süreci Başlıyor ---", "info")
        question_analysis = await self.sequential_think(f"Kullanıcı '{user_input}' diyor.", "SORU_ANALIZI")
        search_decision = await self.sequential_think(f"'{user_input}' için web araması yapmalı mıyım?", "ARAMA_KARARI")
        web_summary = ""
        response_plan = await self.sequential_think(f"Soru: '{user_input}'. Web sonucu: '{'Var' if web_summary else 'Yok'}'. Nasıl cevap vermeliyim?", "CEVAP_PLANLAMA")
        self.log("--- Düşünce Süreci Bitti ---", "info")

        messages_for_groq = [
            {"role": "system", "content": self.create_system_prompt()}
        ]
        for msg in self.conversation_history[-5:]:
            messages_for_groq.append({"role": msg["role"], "content": msg["content"]})
        
        messages_for_groq.append({"role": "user", "content": 
            f"DÜŞÜNCE SÜRECİ:\n- Analiz: {question_analysis}\n- Arama Kararı: {search_decision}\n- Web Özeti: {web_summary}\n- Cevap Planı: {response_plan}\n\nKullanıcı: {user_input}\n\nKarakterine uygun cevabı şimdi ver:"
        })

        self.log("🤖 Final cevap üretiliyor...", "info")
        final_response = await self.call_groq_api(messages_for_groq)
        self.log("✅ Cevap hazır.", "success")
        self.conversation_history.append({"role": "assistant", "content": final_response})
        return final_response

# --- Streamlit Arayüzü ---

st.title("Persona Simülatörü")

@st.cache_resource
def get_agent(persona_name, log_container_key):
    if log_container_key not in st.session_state:
        st.session_state[log_container_key] = []

    def ui_logger(message, type="info"):
        color = {
            "info": "#495057", "success": "#28a745", "warning": "#ffc107",
            "error": "#dc3545", "debug": "#6c757d"
        }.get(type, "black")
        # HTML tag'lerinden kaçınarak logları daha temiz tut
        safe_message = html.escape(message)
        st.session_state[log_container_key].append(f'<span style="color: {color};">{safe_message}</span>')

    return PersonaAgent(persona_name=persona_name, ui_log_callback=ui_logger)

# --- Ajanları ve Durumları Yönetme ---
eski_agent = get_agent("tugrul_bey", "eski_logs")
yeni_agent = get_agent("yeni_tugrul", "yeni_logs")

def generate_chat_html(chat_history):
    chat_html = ""
    for message in chat_history:
        role = message["role"]
        bubble_class = "user-bubble" if role == "user" else "assistant-bubble"
        escaped_content = html.escape(message["content"]).replace('\n', '<br>')
        chat_html += f'<div class="message-bubble {bubble_class}">{escaped_content}</div>'
    return chat_html

def display_chat_column(title, agent, logs_key):
    with st.container():
        st.markdown(f'<div class="chat-header">{title}</div>', unsafe_allow_html=True)
        
        with st.expander("Düşünce Sürecini Göster"):
            logs_html = "<br>".join(st.session_state.get(logs_key, []))
            st.markdown(f'<div class="thinking-box">{logs_html}</div>', unsafe_allow_html=True)

        chat_container = st.container()
        with chat_container:
            chat_html = generate_chat_html(agent.conversation_history)
            st.markdown(f'<div class="chat-container">{chat_html}</div>', unsafe_allow_html=True)

# --- Arayüz Sütunları ---
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="chat-column">', unsafe_allow_html=True)
    display_chat_column("Eski Tuğrul", eski_agent, "eski_logs")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="chat-column">', unsafe_allow_html=True)
    display_chat_column("Yeni Tuğrul", yeni_agent, "yeni_logs")
    st.markdown('</div>', unsafe_allow_html=True)


# --- Ana Sohbet Döngüsü ---
async def run_chat_for_persona(agent, prompt, log_container_key):
    st.session_state[log_container_key].clear()
    response = await agent.chat(prompt)
    return response

async def process_agents_and_get_responses(prompt_to_process):
    st.session_state.eski_logs.clear()
    st.session_state.yeni_logs.clear()

    task1 = asyncio.create_task(run_chat_for_persona(eski_agent, prompt_to_process, "eski_logs"))
    task2 = asyncio.create_task(run_chat_for_persona(yeni_agent, prompt_to_process, "yeni_logs"))

    await asyncio.gather(task1, task2)

    st.session_state.processing_prompt = None 
    st.rerun()

# --- Chat Input ve İşleme Tetikleyici ---
if prompt := st.chat_input("Tuğrullara sor..."):
    eski_agent.conversation_history.append({"role": "user", "content": prompt})
    yeni_agent.conversation_history.append({"role": "user", "content": prompt})
    st.session_state.processing_prompt = prompt
    st.rerun()

# --- İşleme Devam Etme Bloğu ---
if st.session_state.processing_prompt:
    with st.spinner("Agent'lar düşünüyor..."):
        try:
            # Streamlit'in event loop'u ile uyumlu çalışması için
            asyncio.run(process_agents_and_get_responses(st.session_state.processing_prompt))
        except Exception as e:
            st.error(f"Agent işleme sırasında bir hata oluştu: {e}")
            st.session_state.processing_prompt = None 
            st.rerun()