import streamlit as st
import json
import os
import asyncio
import html
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# --- Genel Yapılandırma ---
st.set_page_config(page_title="Microcosmos Simülatörü", layout="wide")
load_dotenv()

# --- Sohbet Geçmişi ve Logları Başlatma (EN ÜSTTE) ---
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

# --- Stil Dosyaları ---
st.markdown("""
<style>
    .stApp {
        background-color: #f0f2f5;
    }
    .main-container {
        padding-top: 1rem;
    }
    .chat-column {
        border-radius: 12px;
        background-color: #ffffff;
        padding: 0;
        height: 85vh;
        display: flex;
        flex-direction: column;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .chat-header {
        font-size: 20px;
        font-weight: bold;
        text-align: center;
        padding: 15px;
        background-color: #075e54;
        color: white;
        border-top-left-radius: 12px;
        border-top-right-radius: 12px;
    }
    .thinking-box {
        background-color: #f8f9fa;
        border-bottom: 1px solid #e0e0e0;
        padding: 10px;
        font-size: 0.85rem;
        color: #495057;
        max-height: 250px;
        overflow-y: auto;
    }
    .chat-container {
        flex-grow: 1;
        overflow-y: auto;
        padding: 15px;
        display: flex;
        flex-direction: column;
    }
    .message-bubble {
        padding: 8px 14px;
        border-radius: 18px;
        margin-bottom: 8px;
        max-width: 85%;
        word-wrap: break-word;
        box-shadow: 0 1px 1px rgba(0,0,0,0.05);
    }
    .user-bubble {
        background-color: #dcf8c6;
        align-self: flex-end;
    }
    .assistant-bubble {
        background-color: #ffffff;
        align-self: flex-start;
        border: 1px solid #f0f0f0;
    }
</style>
""", unsafe_allow_html=True)


# --- PersonaAgent Sınıfı (main.py'dan uyarlandı) ---
class PersonaAgent:
    def __init__(self, persona_name="tugrul_bey", ui_log_callback=None):
        self.persona_name = persona_name
        # Logları doğrudan konsola yazdır
        self.log = lambda message, type: print(f"[{self.persona_name.upper()}][{type.upper()}] {message}")
        
        self.api_keys = self._load_api_keys()
        self.current_api_index = 0
        self.smithery_api_key = os.getenv("SMITHERY_API_KEY")
        self.smithery_profile = os.getenv("SMITHERY_PROFILE")

        if not self.api_keys:
            self.log("Hiçbir GEMINI API key bulunamadı! .env dosyasını kontrol edin.", "error")
            st.stop()
        
        if not self.smithery_api_key or not self.smithery_profile:
            self.log("SMITHERY API bilgileri .env'de bulunamadı. Web arama devre dışı bırakıldı.", "warning")

        self._initialize_model()
        self.persona = self._load_persona(persona_name)
        self.conversation_history = []

    def _load_api_keys(self):
        keys = [key.strip() for key in os.getenv("GEMINI_API_KEY", "").split(',') if key.strip()]
        if not keys:
            single_key = os.getenv("GEMINI_API_KEY")
            if single_key:
                keys.append(single_key)
        return keys

    def _initialize_model(self):
        if not self.api_keys:
            return
        genai.configure(api_key=self.api_keys[self.current_api_index])
        self.model = genai.GenerativeModel('gemini-1.5-flash')

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

    def switch_api_key(self):
        self.log("🔑 API Anahtarı değiştiriliyor...", "info")
        self.current_api_index = (self.current_api_index + 1) % len(self.api_keys)
        self._initialize_model()
        self.log(f"🔄 API KEY DEĞİŞTİRİLDİ: #{self.current_api_index + 1}", "success")

    async def try_with_api_rotation(self, prompt, max_retries=None):
        self.log(f"try_with_api_rotation çağrıldı. Prompt başlangıcı: {prompt[:50]}...", "debug")
        if max_retries is None:
            max_retries = len(self.api_keys)
        
        for attempt in range(max_retries):
            try:
                self.log(f"API çağrısı denemesi {attempt + 1}/{max_retries}...", "debug")
                # await asyncio.sleep(1) # API çağrısını simüle etmek için bekleme
                # return f"DEBUG RESPONSE from {self.persona_name} for prompt: {prompt[:50]}..."
                response = await self.model.generate_content_async(prompt)
                self.log(f"API çağrısı başarılı.", "debug")
                return response.text.strip()
            except Exception as e:
                error_msg = str(e)
                self.log(f"API çağrısı hatası (Deneme {attempt + 1}): {error_msg}", "error")
                if "429" in error_msg or "quota" in error_msg.lower():
                    self.log(f"API #{self.current_api_index + 1} kota aşıldı. Diğer anahtar deneniyor.", "warning")
                    if attempt < max_retries - 1:
                        self.switch_api_key()
                        continue
                raise e # Hatanın yukarıya fırlatılmasını sağla
        self.log("Tüm API denemeleri başarısız oldu.", "error")
        return "Sistem yoğunluğu nedeniyle geçici olarak hizmet veremiyorum."

    def create_system_prompt(self):
        bio_text = "\n- ".join(self.persona.get("bio", ["Bilinmiyor"]))
        style_text = "\n- ".join(self.persona.get("style", {}).get("chat", ["Normal konuşur"]))
        lore_text = "\n- ".join(self.persona.get("lore", [""])[:15])
        knowledge_text = "\n- ".join(self.persona.get("knowledge", [""])[:8])
        return f"""Sen {self.persona.get("name", "Bilinmeyen Karakter")}'sin. Aşağıdaki kimliğin:\n\nBİOGRAFİ:\n- {bio_text}\n\nKONUŞMA TARZI:\n- {style_text}\n\nHAYATA BAKIŞ:\n- {lore_text}\n\nBİLGİN:\n- {knowledge_text}\n\nÖNEMLİ KURALLAR:\n- Karakterine uygun davran\n- Güncel olayları web aramalarından öğreniyorsun\n- Kendi görüşlerini belirt ama saygılı ol\n- Detaylı bilgi ver ama çok uzun olma"""

    async def sequential_think(self, prompt: str, stage_name: str):
        self.log(f"🧠 {stage_name.upper()} DÜŞÜNÜLÜYOR...", "info")
        thinking_prompt = f"'{prompt}' konusunu 2-3 cümleyle düşün: 1. Durum ne? 2. Ne yapmalıyım? 3. Kararım ne?"
        try:
            self.log(f"Sequential Think için API çağrısı başlatılıyor: {stage_name}", "debug")
            result = await self.try_with_api_rotation(thinking_prompt)
            self.log(f"Sequential Think API çağrısı tamamlandı: {stage_name}", "debug")
            self.log(f"💭 {stage_name.upper()} SONUCU: {result}", "success")
            return result
        except Exception as e:
            self.log(f"❌ {stage_name} düşünme hatası: {e}", "error")
            return "Normal bir yaklaşımla cevap vereceğim."

    async def search_web_detailed(self, keywords: str):
        self.log("Web arama fonksiyonu devre dışı bırakıldı.", "warning")
        return ""

    async def chat(self, user_input: str):
        self.log(f"💬 Yeni mesaj alındı: '{user_input}'", "info")
        self.conversation_history.append({"role": "user", "content": user_input})

        self.log("--- Düşünce Süreci Başlıyor ---", "info")

        question_analysis = await self.sequential_think(f"Kullanıcı '{user_input}' diyor.", "SORU_ANALIZI")
        self.log(f"Analiz Sonucu: {question_analysis}", "debug")

        search_decision = await self.sequential_think(f"'{user_input}' için web araması yapmalı mıyım?", "ARAMA_KARARI")
        self.log(f"Arama Kararı: {search_decision}", "debug")
        
        web_summary = ""

        response_plan = await self.sequential_think(f"Soru: '{user_input}'. Web sonucu: '{'Var' if web_summary else 'Yok'}'. Nasıl cevap vermeliyim?", "CEVAP_PLANLAMA")
        self.log(f"Cevap Planı: {response_plan}", "debug")

        history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.conversation_history[-3:]])
        final_prompt = f"{self.create_system_prompt()}\n\nGEÇMİŞ KONUŞMA:\n{history_text}\n\nDÜŞÜNCE SÜRECİ:\n- Analiz: {question_analysis}\n- Arama Kararı: {search_decision}\n- Web Özeti: {web_summary}\n- Cevap Planı: {response_plan}\n\nKullanıcı: \"{user_input}\"\n\nKarakterine uygun cevabı şimdi ver:"
        
        self.log("🤖 Final cevap üretiliyor...", "info")
        final_response = await self.try_with_api_rotation(final_prompt)
        self.log("✅ Cevap hazır.", "success")
        self.conversation_history.append({"role": "assistant", "content": final_response})
        return final_response

# --- Streamlit Arayüzü ---

st.title("Persona Simülatörü: Düşünce Katmanlı Mimari")

@st.cache_resource
def get_agent(persona_name, log_container_key):
    # Her agent için ayrı bir log listesi tut
    if log_container_key not in st.session_state:
        st.session_state[log_container_key] = []

    # Logları doğrudan konsola yazdır
    def ui_logger(message, type="info"):
        print(f"[{persona_name.upper()}][{type.upper()}] {message}")
        # UI'da göstermek için session_state'e de ekle
        color = {
            "info": "#495057",    # Koyu gri
            "success": "#28a745", # Yeşil
            "warning": "#ffc107", # Turuncu
            "error": "#dc3545",   # Kırmızı
            "debug": "#6c757d"    # Açık gri
        }.get(type, "black")
        st.session_state[log_container_key].append(f"<span style=\"color: {color};\">{message}</span>")

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

# --- Arayüz Sütunları ---
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="chat-column">', unsafe_allow_html=True)
    st.markdown('<div class="chat-header">Eski Tuğrul</div>', unsafe_allow_html=True)
    with st.container():
        # Düşünce loglarını göster
        for log_entry in st.session_state.eski_logs:
            st.markdown(log_entry, unsafe_allow_html=True)
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    st.markdown(generate_chat_html(eski_agent.conversation_history), unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="chat-column">', unsafe_allow_html=True)
    st.markdown('<div class="chat-header">Yeni Tuğrul</div>', unsafe_allow_html=True)
    with st.container():
        # Düşünce loglarını göster
        for log_entry in st.session_state.yeni_logs:
            st.markdown(log_entry, unsafe_allow_html=True)
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    st.markdown(generate_chat_html(yeni_agent.conversation_history), unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

# --- Ana Sohbet Döngüsü ---
async def run_chat_for_persona(agent, prompt, log_container_key):
    # Logları temizle
    st.session_state[log_container_key] = []
    response = await agent.chat(prompt)
    return response

async def process_agents_and_get_responses(prompt_to_process):
    print(f"[MAIN] process_agents_and_get_responses başladı. Prompt: {prompt_to_process}")
    # Clear logs for new processing cycle
    st.session_state.eski_logs = []
    st.session_state.yeni_logs = []

    # Run agent tasks
    task1 = asyncio.create_task(run_chat_for_persona(eski_agent, prompt_to_process, "eski_logs"))
    task2 = asyncio.create_task(run_chat_for_persona(yeni_agent, prompt_to_process, "yeni_logs"))

    print("[MAIN] asyncio.gather bekleniyor.")
    await asyncio.gather(task1, task2)
    print("[MAIN] Agent görevleri tamamlandı.")

    # After processing, clear the processing flag and rerun to update UI
    st.session_state.processing_prompt = None # Clear the prompt being processed
    print("[MAIN] İşlem tamamlandı. UI güncellemesi için rerun çağrılıyor.")
    st.rerun()

# --- Chat Input ve İşleme Tetikleyici ---
if prompt := st.chat_input("Tuğrullara sor..."):
    print(f"[MAIN] Chat input algılandı: {prompt}")
    # Add user message to history immediately
    eski_agent.conversation_history.append({"role": "user", "content": prompt})
    yeni_agent.conversation_history.append({"role": "user", "content": prompt})

    # Set flag to trigger processing on next rerun
    st.session_state.processing_prompt = prompt
    print("[MAIN] Kullanıcı mesajları geçmişe eklendi. İşleme bayrağı ayarlandı. İlk rerun çağrılıyor.")
    st.rerun() # Trigger rerun to show user message and start processing

# --- İşleme Devam Etme Bloğu ---
# Bu blok, st.rerun() sonrası betik yeniden başladığında çalışır.
if st.session_state.processing_prompt:
    print(f"[MAIN] Devam eden işlem algılandı: {st.session_state.processing_prompt}")
    with st.spinner("Agent'lar düşünüyor..."):
        try:
            asyncio.run(process_agents_and_get_responses(st.session_state.processing_prompt))
        except Exception as e:
            print(f"[MAIN][ERROR] Agent işleme sırasında hata oluştu: {e}")
            st.error(f"Agent işleme sırasında bir hata oluştu: {e}")
            st.session_state.processing_prompt = None # Hata durumunda bayrağı temizle
            st.rerun() # Hata mesajını göstermek ve spinner'ı kaldırmak için yeniden çalıştır
