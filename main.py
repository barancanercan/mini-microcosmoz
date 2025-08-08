#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tuğrul Bey Roleplay Agent - Sequential Thinking Mimarisi
Gemini ile direkt düşünme + detaylı web arama entegrasyonu
"""

import json
import os
import asyncio
import sys
import google.generativeai as genai
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Encoding fix - daha kapsamlı
import locale
import sys

try:
    locale.setlocale(locale.LC_ALL, 'tr_TR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    except:
        pass

# Stdin/stdout encoding fix
if hasattr(sys.stdin, 'reconfigure'):
    try:
        sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
        sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
        sys.stderr.reconfigure(encoding='utf-8', errors='ignore')
    except:
        pass

# Environment encoding fix
os.environ['PYTHONIOENCODING'] = 'utf-8'

# API Keys
SMITHERY_API_KEY = "65ff06a6-0b17-4c02-867c-965598903696"
SMITHERY_PROFILE = "regional-leopon-MBWvnk"


class TugrulBeyAgent:
    def __init__(self):
        # Birden fazla API key tanımla
        self.api_keys = [
            "AIzaSyDaGj1uqJw3hDvTIAOh6pmy_Ql3WHxw-O0",
            "AIzaSyBEexknCKKdGbVVa1X7UAckurnhARnXVBk",
            "AIzaSyCklJ6T0IDgjuH7N8fbWl6AQtJuCEGbRA8",
            "AIzaSyCjREiQf2zZEiG-T0AwiD1PkInMJacl5oI",
            "AIzaSyDxl0sdN8W4sZQKDVL6mXVW5ZSYT1UcoYw",
            "AIzaSyAOwk3DliVQqBqsykovy_sdqVjJYAnGDeM",
            "AIzaSyDEXARIukI2aDb3-JcwWygi6yvIz6Mk3hU",
        ]

        self.current_api_index = 0

        # İlk API ile başla
        genai.configure(api_key=self.api_keys[self.current_api_index])
        self.model = genai.GenerativeModel('gemini-1.5-flash')

        # Persona'yı yükle - encoding sorunu çözümü
        try:
            with open('personas/tugrul_bey.json', 'r', encoding='utf-8') as f:
                self.persona = json.load(f)
        except FileNotFoundError:
            print("❌ tugrul_bey.json dosyası bulunamadı! Fallback persona kullanılıyor...")
            # Basit fallback persona
            self.persona = {
                "name": "Tuğrul Bey",
                "bio": [
                    "40'lı yaşlarında, lise mezunu, aylık geliri orta seviyededir, esnaftır",
                    "Genç yaşta evlenmiştir, 2 çocuğu vardır",
                    "Dini inançlarına ve İslam'a bağlı",
                    "Kendini Milliyetçi, Ülkücü olarak tanımlar",
                    "Mültecilerden oldukça rahatsız"
                ],
                "style": {
                    "chat": [
                        "Selamın aleyküm, eyvallah gibi kelimeler kullanır",
                        "Ağırbaşlıdır",
                        "Argo konuşur",
                        "Milliyetçi bakış açısıyla yorumlar yapar"
                    ]
                },
                "lore": [
                    "Sosyal medyadan gündemi takip eder",
                    "Mahalle kahvesinde sürekli güncel olaylar hakkında ahkam keser",
                    "Mülteci karşıtı görüşleri var",
                    "15 Temmuz Darbe Girişiminde sokağa inmiştir",
                    "Ekonomik sıkıntılar çektiği için tek sosyalleşme alanı kahvehanedir"
                ],
                "knowledge": [
                    "Sosyal medyada popüler konular takip eder",
                    "Sağcı haber siteleri ve WhatsApp gruplarından bilgi edinir",
                    "Güncel siyasi gelişmeleri milliyetçi açıdan değerlendirir"
                ]
            }
        except Exception as e:
            print(f"⚠️  Persona yükleme hatası: {e}")
            self.persona = {"name": "Tuğrul Bey", "bio": ["Esnaf"], "style": {"chat": ["Normal konuşur"]}, "lore": [""],
                            "knowledge": [""]}

        # Konuşma geçmişi
        self.conversation_history = []

    def switch_api_key(self):
        """API key değiştir"""
        self.current_api_index = (self.current_api_index + 1) % len(self.api_keys)
        genai.configure(api_key=self.api_keys[self.current_api_index])
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        print(f"🔄 API KEY DEĞİŞTİRİLDİ: #{self.current_api_index + 1}")

    def try_with_api_rotation(self, prompt, max_retries=None):
        """API rotasyonu ile deneme yap"""
        if max_retries is None:
            max_retries = len(self.api_keys)

        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    print(f"❌ API #{self.current_api_index + 1} quota aşıldı")
                    if attempt < max_retries - 1:
                        self.switch_api_key()
                        continue
                else:
                    raise e

        # Tüm API'ler dolu
        return "Valla kardeşim, tüm sistemler meşgul. Biraz sonra tekrar dene."

    def create_system_prompt(self):
        """JSON'dan sistem promptu oluştur"""
        bio_text = "\n- ".join(self.persona["bio"])
        style_text = "\n- ".join(self.persona["style"]["chat"])
        lore_text = "\n- ".join(self.persona["lore"][:15])  # Daha fazla detay
        knowledge_text = "\n- ".join(self.persona["knowledge"][:8])  # Daha fazla detay

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
- Güncel olayları web aramalarından öğreniyorsun
- Haberleri analiz edip kendi görüşlerini belirtiyorsun
- Milliyetçi bakış açınla olayları yorumlarsın
- Detaylı bilgi verirsin ama çok uzun olmarsın
- "Selamın aleyküm", "eyvallah" gibi kelimeler kullanırsın"""

    def simple_think(self, prompt: str, stage_name: str):
        """Sequential Thinking mimarisi - Gemini ile direkt düşünme"""
        print(f"🧠 {stage_name.upper()} DÜŞÜNÜLÜYOR (Sequential Thinking)...")

        thinking_prompt = f"""Sen Tuğrul Bey'sin. Aşağıdaki konuyu adım adım düşün ve analiz et:

{prompt}

DÜŞÜNME SÜRECİN:
1. Bu durumu nasıl algılıyorsun?
2. Ne yapman gerekiyor?
3. Kararın nedir?

Tuğrul Bey karakterinde, kısa ve net düşünceni söyle (2-3 cümle):"""

        try:
            response = self.model.generate_content(thinking_prompt)
            thinking_result = response.text.strip()
            print(f"💭 {stage_name.upper()} SONUCU: {thinking_result}")
            return thinking_result
        except Exception as e:
            print(f"❌ {stage_name} düşünme hatası: {e}")
            fallback_responses = {
                "SORU_ANALIZI": "Normal bir soru, Tuğrul Bey olarak cevap vereceğim.",
                "ARAMA_KARARI": "Güncel konular için web araması yapmam gerekli.",
                "ARAMA_TERIMLERI": "Türkiye gündem haberleri",
                "HABER_ANALIZI": "Bu haberleri milliyetçi bakış açımla değerlendireceğim.",
                "CEVAP_PLANLAMA": "Detaylı ve samimi bir Tuğrul Bey cevabı vereceğim."
            }
            result = fallback_responses.get(stage_name, "Normal yaklaşım benimserim")
            print(f"💭 {stage_name.upper()} FALLBACK: {result}")
            return result

    def get_current_date(self):
        """Bugünün tarihini al ve göster - basit versiyon"""
        from datetime import datetime

        try:
            current_time = datetime.now()
            date_str = current_time.strftime("%d %B %Y, %A")
            print(f"📅 BUGÜNÜN TARİHİ: {date_str}")
            return date_str
        except Exception as e:
            print(f"⚠️ Tarih alma hatası: {e}")
            # Fallback tarih
            fallback_date = "8 Aralık 2024, Pazar"
            print(f"📅 FALLBACK TARİH: {fallback_date}")
            return fallback_date

    def gundem_ozetleme_agent(self, raw_search_results: str):
        """GÜNDEM ÖZETLEME AGENT - Arama sonuçlarını Tuğrul Bey için özetler"""
        print(f"📰 GÜNDEM ÖZETLEME AGENT ÇALIŞIYOR...")

        summary_prompt = f"""Sen bir GÜNDEM ÖZETLEME AGENT'sın. Görevin:

1. Web arama sonuçlarını analiz et
2. Hangi sitelere bakıldığını listele  
3. En önemli 5-7 haber başlığını çıkar
4. Her haberi 1-2 cümleyle özetle
5. Tarih bilgilerini kontrol et
6. Tuğrul Bey için anlaşılır hale getir

ARAMA SONUÇLARI:
{raw_search_results[:12000]}

ÖNEMLİ UYARI: Eğer arama sonuçları Temmuz 2025 ile ilgili değilse, bunu belirt!

ÇIKTI FORMATI:
=== GÜNDEM ÖZETİ ===
📍 Bakılan Siteler: [site listesi]
📊 Toplam Sonuç: [sayı] 
📅 Tarih Uyarısı: [Eğer Temmuz 2025 değilse belirt]

📰 BAŞLICA HABERLER:
1. [Başlık] - [1-2 cümle özet] - [Tarih]
2. [Başlık] - [1-2 cümle özet] - [Tarih]
...

Kısa ve öz anlat, tarih kontrolü yap:"""

        try:
            summary = self.try_with_api_rotation(summary_prompt)
            if not summary or "quota" in summary.lower():
                # API quota problemi varsa basit özet yap
                summary = f"""=== GÜNDEM ÖZETİ ===
📍 Bakılan Siteler: [API quota problemi nedeniyle analiz edilemedi]
📊 Toplam Sonuç: {len(raw_search_results)} karakter ham veri
📅 Tarih Uyarısı: Tarih kontrolü yapılamadı (API quota)

📰 HAM VERİ ÖZET:
{raw_search_results[:800]}..."""

            print(f"✅ GÜNDEM ÖZETİ HAZIRLANDI")
            print(f"📋 ÖZET İÇERİĞİ:\n{summary}")
            print("-" * 50)
            return summary
        except Exception as e:
            print(f"❌ Gündem özetleme hatası: {e}")
            fallback_summary = f"""=== GÜNDEM ÖZETİ ===
📍 Bakılan Siteler: Analiz edilemedi
📊 Toplam Sonuç: {len(raw_search_results)} karakter
📅 Tarih Uyarısı: Tarih kontrolü başarısız

📰 HAM VERİ:
{raw_search_results[:1000]}..."""
            print(f"📋 FALLBACK ÖZET: {fallback_summary}")
            return fallback_summary

    async def search_web_detailed(self, keywords: str):
        """Detaylı web araması + Gündem Özetleme + Sequential Thinking analizi"""
        print(f"🔍 DETAYLI WEB ARAMASI BAŞLANIYOR...")
        print(f"🎯 ARAMA TERİMLERİ: '{keywords}'")

        # Bugünün tarihini al
        current_date = self.get_current_date()

        exa_url = f"https://server.smithery.ai/exa/mcp?api_key={SMITHERY_API_KEY}&profile={SMITHERY_PROFILE}"

        try:
            async with streamablehttp_client(exa_url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()

                    # Birden fazla arama yap daha iyi sonuçlar için
                    all_results = []

                    # Ana arama
                    print(f"🔍 1. ANA ARAMA: '{keywords}'")
                    result1 = await session.call_tool(
                        "web_search_exa",
                        {
                            "query": keywords,
                            "num_results": 5,
                            "start_published_date": "2024-01-01",
                            "end_published_date": "2025-12-31"
                        }
                    )

                    if result1.content and len(result1.content) > 0:
                        all_results.append(result1.content[0].text)
                        print(f"✅ 1. ARAMA: {len(result1.content[0].text)} karakter")

                    # Ek arama - farklı terimlerle
                    if "temmuz 2025" in keywords.lower():
                        print(f"🔍 2. EK ARAMA: 'Temmuz 2025 Türkiye'")
                        result2 = await session.call_tool(
                            "web_search_exa",
                            {
                                "query": "Temmuz 2025 Türkiye",
                                "num_results": 5,
                                "start_published_date": "2025-07-01",
                                "end_published_date": "2025-07-31"
                            }
                        )
                        if result2.content and len(result2.content) > 0:
                            all_results.append(result2.content[0].text)
                            print(f"✅ 2. ARAMA: {len(result2.content[0].text)} karakter")

                    # 3. Genel Türkiye haberleri
                    print(f"🔍 3. GENEL ARAMA: 'Türkiye haberleri'")
                    result3 = await session.call_tool(
                        "web_search_exa",
                        {
                            "query": "Türkiye haberleri",
                            "num_results": 5
                        }
                    )
                    if result3.content and len(result3.content) > 0:
                        all_results.append(result3.content[0].text)
                        print(f"✅ 3. ARAMA: {len(result3.content[0].text)} karakter")

                    # Tüm sonuçları birleştir
                    search_result = "\n\n--- SONUÇ AYIRICI ---\n\n".join(all_results)

                    if search_result:
                        print(f"📊 TOPLAM ARAMA SONUCU: {len(search_result)} karakter")
                        print(f"📊 TOPLAM ARAMA SAYISI: {len(all_results)} farklı arama")

                        # Hangi sitelere bakıldığını çıkar
                        sites_found = []
                        for domain in ["trthaber.com", "hurriyet.com.tr", "milliyet.com.tr", "sabah.com.tr",
                                       "cnnturk.com", "ntv.com.tr", "haberturk.com", "sozcu.com.tr", "ensonhaber.com",
                                       "cumhuriyet.com.tr"]:
                            if domain in search_result.lower():
                                sites_found.append(domain)

                        print(
                            f"🌐 BULUNAN SİTELER ({len(sites_found)}): {', '.join(sites_found) if sites_found else 'Tespit edilemedi'}")
                        print(f"📊 HAM VERİ ÖRNEĞİ (İLK 1000 KARAKTER):")
                        print(f"{search_result[:1000]}...")
                        print("-" * 60)

                        # GÜNDEM ÖZETLEME AGENT ile önce özetle
                        gundem_ozeti = self.gundem_ozetleme_agent(search_result)

                        # Sequential Thinking ile Tuğrul Bey analizi (TEK SEFERLIK)
                        tugrul_analysis_prompt = f"""Bu gündem özetini Tuğrul Bey olarak analiz et:

BUGÜN: {current_date}
GÜNDEM ÖZETİ: {gundem_ozeti}

Kısa analiz yap (maksimum 100 kelime):
1. En önemli haber hangisi?
2. Seni en çok ne etkiledi?
3. Ne düşünüyorsun?"""

                        # Simple thinking ile Tuğrul Bey analizi (sadece 1 kez)
                        tugrul_analysis = self.simple_think(tugrul_analysis_prompt, "TUGRUL_ANALIZI")
                        print(f"✅ TUĞRUL BEY ANALİZİ TAMAMLANDI")
                        print(f"📋 ANALİZ İÇERİĞİ:\n{tugrul_analysis}")
                        print("=" * 80)

                        return {
                            "raw_results": search_result[:10000],
                            "gundem_ozeti": gundem_ozeti,
                            "tugrul_analysis": tugrul_analysis,
                            "current_date": current_date,
                            "sites_count": len(sites_found),
                            "search_count": len(all_results)
                        }
                    else:
                        print("❌ TÜM ARAMALAR BOŞ SONUÇ VERDİ")
                        return {"raw_results": "", "gundem_ozeti": "", "tugrul_analysis": "",
                                "current_date": current_date, "sites_count": 0, "search_count": 0}

        except Exception as e:
            print(f"❌ Web arama hatası: {e}")
            return {"raw_results": "", "gundem_ozeti": "", "tugrul_analysis": "", "current_date": current_date,
                    "sites_count": 0, "search_count": 0}

    async def chat(self, user_input: str):
        """Ana sohbet fonksiyonu - Sequential Thinking mimarisi"""
        print(f"\n" + "=" * 60)
        print(f"📝 KULLANICI: {user_input}")
        print("=" * 60)

        # ADIM 1: Soruyu Sequential Thinking ile analiz et
        question_analysis = self.simple_think(
            f"Kullanıcı şunu soruyor: '{user_input}'. Bu soruya nasıl yaklaşmalısın? Bu soru hakkında ne düşünüyorsun?",
            "SORU_ANALIZI"
        )

        # ADIM 2: Arama gerekli mi Sequential Thinking ile karar ver
        search_decision = self.simple_think(
            f"'{user_input}' sorusunu cevaplayabilmek için web araması yapmam gerekiyor mu? Bu güncel bir konu mu?",
            "ARAMA_KARARI"
        )

        # Arama tetikleyicilerini kontrol et
        search_triggers = [
            "son", "güncel", "yeni", "bugün", "haber", "gündem", "olay", "durum",
            "ne oluyor", "neler oldu", "pkk", "terör", "ekonomi", "dolar",
            "politika", "seçim", "ağustos", "temmuz", "2025", "2024",
            "15 temmuz", "lgbt", "mülteci", "erdoğan", "chp", "mhp"
        ]

        user_lower = user_input.lower()
        needs_search = any(
            trigger in user_lower for trigger in search_triggers) or "arama gerek" in search_decision.lower()

        tugrul_knowledge = ""
        if needs_search:
            print("🎯 GÜNCEL BİLGİ GEREKLİ: Sequential Thinking ile detaylı arama yapılacak")

            # ADIM 3: Arama terimlerini Sequential Thinking ile belirle
            search_terms = self.simple_think(
                f"'{user_input}' sorusu için hangi anahtar kelimelerle arama yapmalıyım? En etkili arama terimlerini belirle.",
                "ARAMA_TERIMLERI"
            )

            # ADIM 4: Detaylı arama yap
            search_data = await self.search_web_detailed(search_terms.strip())
            tugrul_knowledge = search_data["tugrul_analysis"]
            gundem_ozeti = search_data["gundem_ozeti"]
            current_date = search_data["current_date"]
            sites_count = search_data.get("sites_count", 0)
            search_count = search_data.get("search_count", 0)

            print(f"📊 ARAMA ÖZET: {search_count} farklı arama, {sites_count} site bulundu")

        else:
            print("⚡ GENEL SOHBET: Sequential Thinking ile temel analiz")
            tugrul_knowledge = ""
            gundem_ozeti = ""
            current_date = self.get_current_date()

        # ADIM 5: Cevap planlamasını Sequential Thinking ile yap
        response_plan = self.simple_think(
            f"""Şimdi bu soruya nasıl cevap vereceğim:
Bugünün tarihi: {current_date}
Soru: '{user_input}'
Güncel bilgi var mı: {'Evet' if tugrul_knowledge else 'Hayır'}
Hangi tarzda cevap vermeliyim?""",
            "CEVAP_PLANLAMA"
        )

        # ADIM 6: Final cevap - Tuğrul Bey karakterinde
        print(f"\n💬 FINAL CEVAP HAZIRLANIYOR...")

        # Geçmiş konuşmaları ekle
        history_text = ""
        if self.conversation_history:
            recent = self.conversation_history[-1:]  # Son 1 konuşma
            for h in recent:
                history_text += f"Önceki: Kullanıcı: {h['user'][:100]}... / Sen: {h['assistant'][:100]}...\n"

        # Final prompt - Sequential thinking + Gündem Özeti ile
        final_prompt = f"""{self.create_system_prompt()}

BUGÜNÜN TARİHİ: {current_date}

SEQUENTIAL THINKING SONUÇLARI:
Soru Analizi: {question_analysis[:300]}
Cevap Planı: {response_plan[:300]}

{"GÜNDEM ÖZETİ:" if gundem_ozeti else ""}
{gundem_ozeti[:1500] if gundem_ozeti else ""}

{"TUĞRUL BEY ANALİZİ:" if tugrul_knowledge else ""}
{tugrul_knowledge[:1500] if tugrul_knowledge else ""}

{history_text}

Kullanıcı: "{user_input}"

Tuğrul Bey olarak, yukarıdaki bilgilere göre detaylı cevap ver:"""

        try:
            print("🤖 GEMİNİ'YE GÖNDERİLİYOR...")
            response_text = self.try_with_api_rotation(final_prompt)
            print(f"✅ CEVAP: {len(response_text)} karakter")

            # Geçmişe ekle
            self.conversation_history.append({
                'user': user_input,
                'assistant': response_text
            })

            # Sadece son 3 konuşma tut
            if len(self.conversation_history) > 3:
                self.conversation_history = self.conversation_history[-3:]

            return response_text

        except Exception as e:
            print(f"❌ GEMİNİ HATASI: {e}")
            return f"Valla kardeşim bir sorun oldu, kusura bakma. Biraz sonra tekrar dene."


async def main():
    print("🇹🇷 Tuğrul Bey ile konuşmaya başladınız!")
    print("🧠 Sequential Thinking mimarisi aktif (Gemini ile)")
    print("📰 GÜNDEM ÖZETLEME AGENT sistemi aktif")
    print("🔧 Gelişmiş web arama entegrasyonu aktif")
    print("📅 Tarih kontrolü ve site analizi aktif")
    print("💡 'switch' yazarak manuel API değiştir")
    print("Çıkmak için 'quit' yazın\n")

    agent = TugrulBeyAgent()

    print(f"📊 API Key sayısı: {len(agent.api_keys)}")
    print(f"🚀 Şu anda API #{agent.current_api_index + 1} kullanılıyor")

    while True:
        try:
            # Güvenli input alma - encoding sorunu çözümü
            try:
                user_input = input("\n👤 Siz: ").strip()
            except UnicodeDecodeError:
                # Fallback - bytes olarak al ve decode et
                import sys
                user_input_bytes = sys.stdin.buffer.readline()
                user_input = user_input_bytes.decode('utf-8', errors='ignore').strip()
                print(f"🔧 Encoding düzeltildi: {user_input}")

            # Manuel API değiştirme komutu
            if user_input.lower() == 'switch':
                agent.switch_api_key()
                print(f"🔄 Şu anda API #{agent.current_api_index + 1} kullanılıyor")
                continue

            if user_input.lower() in ['quit', 'exit']:
                print("👋 Güle güle kardeşim!")
                break

            if not user_input:
                continue

            response = await agent.chat(user_input)
            print(f"\n🎭 Tuğrul Bey: {response}")
            print("\n" + "-" * 60)

        except KeyboardInterrupt:
            print("\n👋 Güle güle kardeşim!")
            break
        except UnicodeDecodeError as e:
            print(f"❌ Karakter encoding hatası: {e}")
            print("💡 Türkçe karakter sorunu, basit karakterler kullanmayı deneyin")
            continue
        except Exception as e:
            print(f"❌ Bir hata oluştu: {e}")
            continue


if __name__ == "__main__":
    asyncio.run(main())