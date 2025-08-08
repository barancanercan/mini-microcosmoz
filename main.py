#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mini Microcosmos - AI Persona Simulator
Sequential Thinking mimarisi ile güvenli ve yapılandırılmış persona simülasyonu
"""

import json
import os
import asyncio
import sys
import locale
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Environment değişkenlerini yükle
load_dotenv()


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


class PersonaAgent:
    def __init__(self, persona_name="tugrul_bey"):
        """
        Persona tabanlı AI agent
        Args:
            persona_name: personas/ klasöründeki JSON dosya adı
        """
        setup_encoding()

        # API keys'leri environment'tan al
        self.api_keys = self._load_api_keys()
        self.current_api_index = 0

        # Smithery API yapılandırması
        self.smithery_api_key = os.getenv("SMITHERY_API_KEY")
        self.smithery_profile = os.getenv("SMITHERY_PROFILE")

        if not self.smithery_api_key or not self.smithery_profile:
            print("⚠️ SMITHERY API bilgileri .env dosyasında bulunamadı!")
            print("💡 Web arama işlevselliği çalışmayabilir")

        # Gemini modelini başlat
        self._initialize_model()

        # Persona'yı yükle
        self.persona = self._load_persona(persona_name)

        # Konuşma geçmişi
        self.conversation_history = []

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
            raise ValueError("❌ Hiçbir GEMINI API key bulunamadı! .env dosyasını kontrol edin.")

        return api_keys

    def _initialize_model(self):
        """Gemini modelini başlat"""
        genai.configure(api_key=self.api_keys[self.current_api_index])
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def _load_persona(self, persona_name):
        """Persona JSON dosyasını yükle"""
        try:
            with open(f'personas/{persona_name}.json', 'r', encoding='utf-8') as f:
                persona = json.load(f)
                print(f"✅ {persona['name']} persona'sı yüklendi")
                return persona
        except FileNotFoundError:
            print(f"❌ personas/{persona_name}.json dosyası bulunamadı!")
            return self._get_fallback_persona(persona_name)
        except Exception as e:
            print(f"⚠️ Persona yükleme hatası: {e}")
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
        print(f"🔄 API KEY DEĞİŞTİRİLDİ: #{self.current_api_index + 1}")

    def try_with_api_rotation(self, prompt, max_retries=None):
        """API rotasyonu ile güvenli deneme"""
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

    def sequential_think(self, prompt: str, stage_name: str):
        """Sequential Thinking adımı"""
        print(f"🧠 {stage_name.upper()} DÜŞÜNÜLÜYOR...")

        thinking_prompt = f"""Sen {self.persona['name']}'sin. Aşağıdaki konuyu adım adım düşün:

{prompt}

DÜŞÜNME SÜRECİN:
1. Bu durumu nasıl algılıyorsun?
2. Ne yapman gerekiyor?
3. Kararın nedir?

Kısa ve net düşünceni söyle (2-3 cümle):"""

        try:
            result = self.try_with_api_rotation(thinking_prompt)
            print(f"💭 {stage_name.upper()} SONUCU: {result}")
            return result
        except Exception as e:
            print(f"❌ {stage_name} düşünme hatası: {e}")
            fallback_responses = {
                "SORU_ANALIZI": "Normal bir soru, karakterime uygun cevap vereceğim.",
                "ARAMA_KARARI": "Güncel konular için web araması gerekebilir.",
                "ARAMA_TERIMLERI": "Türkiye gündem haberleri",
                "HABER_ANALIZI": "Haberleri kendi perspektifimden değerlendireceğim.",
                "CEVAP_PLANLAMA": "Detaylı ve samimi bir cevap vereceğim."
            }
            result = fallback_responses.get(stage_name, "Normal yaklaşım benimserim")
            print(f"💭 {stage_name.upper()} FALLBACK: {result}")
            return result

    def get_current_date(self):
        """Güncel tarihi al"""
        try:
            current_time = datetime.now()
            date_str = current_time.strftime("%d %B %Y, %A")
            print(f"📅 BUGÜNÜN TARİHİ: {date_str}")
            return date_str
        except Exception as e:
            print(f"⚠️ Tarih alma hatası: {e}")
            fallback_date = "Bilinmeyen Tarih"
            print(f"📅 FALLBACK TARİH: {fallback_date}")
            return fallback_date

    def summarize_comprehensive_news(self, raw_search_results: str, search_count: int, sites_count: int):
        """Kapsamlı haber özetleme - çoklu kaynak analizi"""
        print(f"📰 KAPSAMLI HABER ANALİZİ: {search_count} arama, {sites_count} site")

        summary_prompt = f"""Sen profesyonel bir HABER ANALİZ UZMANISSIN. Görevin:

{search_count} farklı aramadan ve {sites_count} farklı haber sitesinden toplanan verileri analiz et:

KAPSAMLI ARAMA SONUÇLARI:
{raw_search_results[:20000]}

DETAYLI ANALİZ GEREKSİNİMLERİ:
1. Hangi haber sitelerinden bilgi toplandığını tespit et
2. En önemli 8-10 haber başlığını çıkar
3. Her haberi 2-3 cümleyle detaylı özetle
4. Tarih bilgilerini kontrol et ve grupla
5. Haber kategorilerini belirle (ekonomi, siyaset, sosyal, vs.)
6. Çelişkili bilgiler varsa belirt
7. Eksik veya belirsiz konuları işaretle

ÇIKTI FORMATI:
=== KAPSAMLI GÜNDEM ANALİZİ ===
📊 Araştırma Kapsamı: {search_count} arama, {sites_count} farklı kaynak
📍 Taranan Siteler: [tespit edilen site listesi]
📅 Tarih Aralığı: [bulunan tarih aralığı]
📋 Kategori Dağılımı: [ekonomi: X haber, siyaset: Y haber, vs.]

📰 BAŞLICA HABERLER:
1. [KATEGORİ] [Başlık] - [2-3 cümle detaylı özet] - [Kaynak] - [Tarih]
2. [KATEGORİ] [Başlık] - [2-3 cümle detaylı özet] - [Kaynak] - [Tarih]
...

🔍 ANALİZ NOTLARI:
- Çelişkili bilgiler: [varsa belirt]
- Eksik konular: [belirt]
- Güvenilirlik: [genel değerlendirme]

Kapsamlı ve detaylı analiz yap:"""

        try:
            summary = self.try_with_api_rotation(summary_prompt)
            if not summary or "quota" in summary.lower():
                return self._create_fallback_summary(raw_search_results, search_count, sites_count)

            print("✅ KAPSAMLI HABER ANALİZİ TAMAMLANDI")
            return summary

        except Exception as e:
            print(f"❌ Kapsamlı analiz hatası: {e}")
            return self._create_fallback_summary(raw_search_results, search_count, sites_count)

    def _create_fallback_summary(self, raw_data: str, search_count: int, sites_count: int):
        """Fallback haber özeti"""
        return f"""=== KAPSAMLI GÜNDEM ANALİZİ ===
📊 Araştırma Kapsamı: {search_count} arama, {sites_count} site
📍 Taranan Siteler: Analiz edilemedi (API quota)
📅 Tarih Aralığı: Tespit edilemedi
📋 Kategori Dağılımı: Belirlenemedi

📰 HAM VERİ ÖZETİ:
{raw_data[:2000]}...

🔍 ANALİZ NOTLARI:
- Sistem yoğunluğu nedeniyle detaylı analiz yapılamadı
- Ham veriler mevcut, manuel inceleme gerekebilir"""

    async def search_web_detailed(self, keywords: str):
        """Kapsamlı web araması - 10+ site taraması"""
        if not self.smithery_api_key or not self.smithery_profile:
            print("❌ Web arama yapılandırması eksik")
            return {
                "raw_results": "",
                "news_summary": "",
                "analysis": "",
                "current_date": self.get_current_date(),
                "sites_count": 0,
                "search_count": 0
            }

        print(f"🔍 KAPSAMLI WEB ARAMASI BAŞLANIYOR: '{keywords}'")
        current_date = self.get_current_date()

        exa_url = f"https://server.smithery.ai/exa/mcp?api_key={self.smithery_api_key}&profile={self.smithery_profile}"

        try:
            async with streamablehttp_client(exa_url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()

                    all_results = []

                    # Çoklu arama stratejisi - 8 farklı arama
                    search_queries = [
                        # 1. Ana arama
                        {"query": keywords, "num_results": 8, "label": "ANA ARAMA"},

                        # 2. Güncel Türkiye haberleri
                        {"query": "Türkiye haberleri gündem", "num_results": 6, "label": "GÜNCEL HABERLER"},

                        # 3. Ekonomi odaklı
                        {"query": f"{keywords} ekonomi", "num_results": 5, "label": "EKONOMİ ARAMASI"},

                        # 4. Politik gelişmeler
                        {"query": f"{keywords} siyaset politik", "num_results": 5, "label": "SİYASET ARAMASI"},

                        # 5. Sosyal gelişmeler
                        {"query": f"{keywords} toplum sosyal", "num_results": 4, "label": "SOSYAL ARAMASI"},

                        # 6. Son dakika haberleri
                        {"query": "son dakika Türkiye", "num_results": 6, "label": "SON DAKİKA"},

                        # 7. Özel tarih araması (eğer tarih belirtilmişse)
                        {"query": f"Türkiye 2023 2024 2025 haber", "num_results": 5, "label": "TARİH ARAMASI"},

                        # 8. Genel gündem
                        {"query": "Türkiye gündem analiz", "num_results": 4, "label": "GÜNDEM ANALİZİ"}
                    ]

                    print(f"🎯 TOPLAM {len(search_queries)} FARKLI ARAMA YAPILACAK")

                    for i, search_config in enumerate(search_queries, 1):
                        try:
                            print(f"🔍 {i}. {search_config['label']}: '{search_config['query']}'")

                            # Arama parametreleri
                            search_params = {
                                "query": search_config["query"],
                                "num_results": search_config["num_results"]
                            }

                            # Tarih filtresi ekle (sadece spesifik aramalar için)
                            if "2023" in keywords.lower() or "2024" in keywords.lower():
                                search_params["start_published_date"] = "2023-01-01"
                                search_params["end_published_date"] = "2025-12-31"
                            elif i <= 4:  # İlk 4 arama için tarih filtresi
                                search_params["start_published_date"] = "2024-01-01"
                                search_params["end_published_date"] = "2025-12-31"

                            result = await session.call_tool("web_search_exa", search_params)

                            if result.content and len(result.content) > 0:
                                all_results.append(result.content[0].text)
                                print(f"✅ {i}. ARAMA: {len(result.content[0].text)} karakter")
                            else:
                                print(f"⚠️ {i}. ARAMA: Sonuç bulunamadı")

                            # API rate limiting için kısa bekleyiş
                            await asyncio.sleep(0.2)

                        except Exception as e:
                            print(f"❌ {i}. ARAMA HATASI: {e}")
                            continue

                    # Sonuçları birleştir
                    search_result = "\n\n--- ARAMA SONUCU AYIRICI ---\n\n".join(all_results)

                    if search_result:
                        print(f"📊 TOPLAM ARAMA SONUCU: {len(search_result)} karakter")
                        print(f"📊 BAŞARILI ARAMA SAYISI: {len(all_results)}")

                        # Kapsamlı site analizi
                        turkish_domains = [
                            "trthaber.com", "hurriyet.com.tr", "milliyet.com.tr",
                            "sabah.com.tr", "cnnturk.com", "ntv.com.tr",
                            "haberturk.com", "sozcu.com.tr", "ensonhaber.com",
                            "cumhuriyet.com.tr", "yenisakaryahaber.com.tr", "gazetevatan.com",
                            "aksam.com.tr", "star.com.tr", "yenisafak.com",
                            "takvim.com.tr", "posta.com.tr", "turkiyegazetesi.com.tr",
                            "dunya.com", "aa.com.tr", "bbc.com/turkce"
                        ]

                        sites_found = [domain for domain in turkish_domains
                                       if domain in search_result.lower()]

                        # Site çeşitliliği analizi
                        print(f"🌐 TARANAN SİTE SAYISI: {len(sites_found)}")
                        if sites_found:
                            print(f"🔗 BULUNAN SİTELER: {', '.join(sites_found)}")
                        else:
                            print("🔗 BULUNAN SİTELER: Site analizi yapılamadı")

                        # İçerik analizi için sample göster
                        print(f"📄 İÇERİK ÖRNEĞİ (İLK 2000 KARAKTER):")
                        print(f"{search_result[:2000]}...")
                        print("=" * 80)

                        # Kapsamlı haber özetleme
                        print("📰 KAPSAMLI HABER ÖZETLEMESİ BAŞLANIYOR...")
                        news_summary = self.summarize_comprehensive_news(search_result, len(all_results),
                                                                         len(sites_found))

                        # Detaylı persona analizi
                        analysis_prompt = f"""Bu kapsamlı araştırma sonuçlarını {self.persona['name']} olarak analiz et:

BUGÜN: {current_date}
TOPLAM ARAMA: {len(all_results)} farklı arama
BULUNAN SİTE: {len(sites_found)} farklı haber sitesi

KAPSAMLI HABER ÖZETİ:
{news_summary[:2000]}

Detaylı analiz yap (150 kelimeye kadar):
1. En dikkat çeken gelişme nedir?
2. Kişisel olarak seni en çok etkileyen konu?
3. Bu gelişmelerin ülkeye etkisi nedir?
4. Genel değerlendirmen ve yorumun?"""

                        analysis = self.sequential_think(analysis_prompt, "DETAYLI_ANALIZ")

                        return {
                            "raw_results": search_result[:15000],  # Daha fazla veri
                            "news_summary": news_summary,
                            "analysis": analysis,
                            "current_date": current_date,
                            "sites_count": len(sites_found),
                            "search_count": len(all_results)
                        }
                    else:
                        print("❌ TÜM ARAMALAR BAŞARISIZ")
                        return {
                            "raw_results": "",
                            "news_summary": "",
                            "analysis": "",
                            "current_date": current_date,
                            "sites_count": 0,
                            "search_count": 0
                        }

        except Exception as e:
            print(f"❌ Web arama hatası: {e}")
            return {
                "raw_results": "",
                "news_summary": "",
                "analysis": "",
                "current_date": current_date,
                "sites_count": 0,
                "search_count": 0
            }

    async def chat(self, user_input: str):
        """Ana sohbet fonksiyonu"""
        print(f"\n{'=' * 60}")
        print(f"📝 KULLANICI: {user_input}")
        print("=" * 60)

        # Sequential Thinking pipeline
        question_analysis = self.sequential_think(
            f"Kullanıcı '{user_input}' diyor. Bu soruya nasıl yaklaşmalısın?",
            "SORU_ANALIZI"
        )

        search_decision = self.sequential_think(
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
            print("🎯 GÜNCEL BİLGİ ARANACAK")

            search_terms = self.sequential_think(
                f"'{user_input}' için en iyi arama terimleri neler?",
                "ARAMA_TERIMLERI"
            )

            search_data = await self.search_web_detailed(search_terms.strip())
            analysis = search_data["analysis"]
            news_summary = search_data["news_summary"]

            print(f"📊 ARAMA ÖZETİ: {search_data['search_count']} arama, {search_data['sites_count']} site")
        else:
            print("⚡ GENEL SOHBET")

        # Cevap planlama
        response_plan = self.sequential_think(
            f"Soru: '{user_input}' | Güncel bilgi: {'Var' if analysis else 'Yok'} | Nasıl cevap vereyim?",
            "CEVAP_PLANLAMA"
        )

        # Final cevap
        print("💬 CEVAP HAZIRLANIYOR...")

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
            print("🤖 CEVAP ÜRETİLİYOR...")
            response_text = self.try_with_api_rotation(final_prompt)
            print(f"✅ CEVAP HAZIR: {len(response_text)} karakter")

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
            print(f"❌ CEVAP ÜRETME HATASI: {e}")
            return "Özür dilerim, şu anda teknik bir sorun yaşıyorum. Lütfen biraz sonra tekrar deneyin."


def get_available_personas():
    """Mevcut persona'ları listele"""
    try:
        personas = []
        for file in os.listdir('personas'):
            if file.endswith('.json'):
                personas.append(file[:-5])  # .json uzantısını çıkar
        return personas
    except:
        return ['tugrul_bey']


async def main():
    """Ana program"""
    print("🎭 Mini Microcosmos - AI Persona Simulator")
    print("🧠 Sequential Thinking mimarisi aktif")
    print("🔧 Güvenli ve yapılandırılmış sistem\n")

    # Mevcut persona'ları göster
    available_personas = get_available_personas()
    print(f"📋 Mevcut Persona'lar: {', '.join(available_personas)}")

    # Persona seçimi (varsayılan: tugrul_bey)
    selected_persona = "tugrul_bey"
    print(f"🎯 Aktif Persona: {selected_persona}")

    try:
        agent = PersonaAgent(selected_persona)
        print(f"📊 API Key sayısı: {len(agent.api_keys)}")
        print("💡 Komutlar: 'switch' (API değiştir), 'quit' (çıkış)\n")
    except Exception as e:
        print(f"❌ Agent başlatma hatası: {e}")
        return

    while True:
        try:
            user_input = input(f"\n👤 Siz: ").strip()

            if user_input.lower() == 'switch':
                agent.switch_api_key()
                continue

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Görüşmek üzere!")
                break

            if not user_input:
                continue

            response = await agent.chat(user_input)
            print(f"\n🎭 {agent.persona['name']}: {response}")
            print("\n" + "-" * 60)

        except KeyboardInterrupt:
            print("\n👋 Görüşmek üzere!")
            break
        except Exception as e:
            print(f"❌ Hata: {e}")
            continue


if __name__ == "__main__":
    asyncio.run(main())