import streamlit as st
import json
import os
import asyncio
import html
import aiohttp
from datetime import datetime
from dotenv import load_dotenv
from groq import AsyncGroq


# --- PersonaAgent Sınıfı (Düzeltilmiş Versiyon) ---
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

    # ========== WEB ARAMA FONKSİYONU (BASİTLEŞTİRİLMİŞ) ==========
    async def web_search_mcp(self, query: str) -> str:
        """Basit web araması yapar - DuckDuckGo API kullanır"""
        try:
            self.log(f"🔍 Web araması başlatılıyor: '{query}'", "info")

            # DuckDuckGo Instant Answer API
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = self._format_duckduckgo_results(data, query)
                        if result:
                            self.log("✅ Web araması başarılı", "success")
                            return result

            # Eğer sonuç yoksa basit mesaj döndür
            self.log("Web araması sonuç döndürmedi", "warning")
            return f"'{query}' konusunda web araması yapıldı ancak detaylı sonuç alınamadı."

        except Exception as e:
            self.log(f"❌ Web araması hatası: {e}", "error")
            return f"'{query}' konusunda arama yapılmaya çalışıldı ancak teknik sorun oluştu."

    def _format_duckduckgo_results(self, data, query) -> str:
        """DuckDuckGo sonuçlarını formatlar"""
        result = f"🔍 '{query}' ARAMA SONUÇLARI:\n\n"

        # Abstract (özet bilgi)
        if data.get("Abstract"):
            result += f"📄 **Özet Bilgi:**\n{data['Abstract']}\n\n"

        # Definition (tanım)
        if data.get("Definition"):
            result += f"📚 **Tanım:**\n{data['Definition']}\n\n"

        # Related topics
        if data.get("RelatedTopics"):
            result += "🔗 **İlgili Konular:**\n"
            for topic in data["RelatedTopics"][:3]:
                if isinstance(topic, dict) and topic.get("Text"):
                    result += f"- {topic['Text'][:100]}...\n"
            result += "\n"

        # Eğer hiçbir sonuç yoksa
        if len(result.strip()) <= len(f"🔍 '{query}' ARAMA SONUÇLARI:"):
            return None

        return result[:800]  # Sınırla

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
- Web arama sonuçlarını kullanarak güncel bilgi ver
- Kendi görüşlerini belirt ama saygılı ol
- Detaylı bilgi ver ama çok uzun olma
- Web araması yapıldığında sonuçları değerlendir ve yorumla"""

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

    # ========== ANA CHAT FONKSİYONU (DÜZELTİLMİŞ) ==========
    async def chat(self, user_input: str):
        self.log(f"💬 Yeni mesaj alındı: '{user_input}'", "info")
        self.conversation_history.append({"role": "user", "content": user_input})

        self.log("--- Düşünce Süreci Başlıyor ---", "info")

        # 1. Soru analizi
        question_analysis = await self.sequential_think(
            f"Kullanıcı '{user_input}' diyor.",
            "SORU_ANALIZI"
        )

        # 2. Arama kararı
        search_decision = await self.sequential_think(
            f"'{user_input}' için web araması yapmalı mıyım? Güncel bilgi gerekli mi?",
            "ARAMA_KARARI"
        )

        # 3. Web arama (gerekirse)
        web_summary = ""
        if "evet" in search_decision.lower() or "gerekli" in search_decision.lower():
            self.log("🔍 WEB ARAMASI YAPILIYOR...", "info")
            # Arama terimlerini belirle
            search_terms = await self.sequential_think(
                f"'{user_input}' sorusu için hangi kelimeleri aratmalıyım? Sadece anahtar kelimeleri söyle.",
                "ARAMA_TERİMLERİ"
            )

            # Web araması yap
            web_summary = await self.web_search_mcp(search_terms)
            self.log(f"📄 WEB SONUÇLARI ALINDI: {len(web_summary)} karakter", "success")
        else:
            self.log("📵 Web araması gerekli görülmedi", "info")

        # 4. Cevap planlaması
        response_plan = await self.sequential_think(
            f"Soru: '{user_input}'. Web sonucu: '{web_summary[:200] if web_summary else 'Yok'}'. Nasıl cevap vermeliyim?",
            "CEVAP_PLANLAMA"
        )

        self.log("--- Düşünce Süreci Bitti ---", "info")

        # Final cevap oluşturma
        messages_for_groq = [
            {"role": "system", "content": self.create_system_prompt()}
        ]

        # Geçmiş konuşmaları ekle (son 5 mesaj)
        for msg in self.conversation_history[-5:]:
            messages_for_groq.append({"role": msg["role"], "content": msg["content"]})

        # Ana prompt'u oluştur
        web_info = f"WEB ARAMA SONUÇLARI:\n{web_summary}\n" if web_summary else ""

        final_prompt = f"""DÜŞÜNCE SÜRECİ:
- Analiz: {question_analysis}
- Arama Kararı: {search_decision}
- Cevap Planı: {response_plan}

{web_info}

Kullanıcı: {user_input}

Yukarıdaki bilgileri kullanarak karakterine uygun, detaylı ve yararlı bir cevap ver. 
Web arama sonuçları varsa bunları mutlaka yorumla ve değerlendir."""

        messages_for_groq.append({"role": "user", "content": final_prompt})

        self.log("🤖 Final cevap üretiliyor...", "info")
        final_response = await self.call_groq_api(messages_for_groq)
        self.log("✅ Cevap hazır.", "success")

        self.conversation_history.append({"role": "assistant", "content": final_response})
        return final_response