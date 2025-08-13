# 🎭 Mini Microcosmos - AI Persona Simulator

Türkiye'deki kararsız-küskün seçmen profillerini **Sequential Thinking** mimarisi ile simüle eden AI projesi.

## ✨ Özellikler

- **🧠 Sequential Thinking Pipeline**: 7 aşamalı düşünce süreci
- **🔍 Gerçek Zamanlı Web Araması**: MCP protokolü ile güncel bilgi
- **🎭 Çoklu Persona**: Farklı seçmen profillerinde AI ajanları  
- **⚡ Paralel İşlem**: Aynı anda iki persona ile sohbet
- **📊 Detaylı Logging**: Tüm düşünce süreçlerini izleme

## 🚀 Hızlı Başlangıç

### 1. Kurulum
```bash
git clone <repo-url>
cd mini-microcozmos
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 2. API Keys Ayarlama
```bash
cp config/.env.example config/.env
```

`config/.env` dosyasına API keylerini ekleyin:
```env
GEMINI_API_KEY=your_gemini_api_key_here
SMITHERY_API_KEY=your_smithery_api_key  
SMITHERY_PROFILE=your_smithery_profile
```

### 3. Çalıştırma
```bash
streamlit run src/ui/streamlit_app_groq.py
```

## 🎯 Persona'lar

### Mevcut Karakterler:
- **🎯 Eski Tuğrul**: MHP/Ülkücü, milliyetçi esnaf
- **🔄 Yeni Tuğrul**: CHP'ye geçiş yapan, değişen profil
- **👵 Hatice Teyze**: Muhafazakar, 61 yaşında ev hanımı  
- **👩 Elif**: 23 yaşında üniversiteli, feminist
- **👨 Kenan Bey**: 36 yaşında, Kemalist, eğitimli

## 🧠 Sequential Thinking Pipeline

Sistem her soruya 7 aşamalı düşünce süreci uygular:

1. **📝 SORU_ANALIZI** - Kullanıcı isteğini anlama
2. **🔍 ARAMA_KARARI** - Web araması gerekli mi?
3. **🎯 ARAMA_TERIMLERI** - En uygun anahtar kelimeler
4. **📡 WEB ARAMA** - 4 farklı kaynaktan veri toplama
5. **📰 HABER_ANALIZI** - Sonuçları persona perspektifinden değerlendirme
6. **📋 CEVAP_PLANLAMA** - Response stratejisini belirleme
7. **💬 FINAL_CEVAP** - Karakter uygun yanıt üretme

## 🔧 Teknoloji Stack

- **🤖 AI Model**: Google Gemini 1.5 Flash
- **🌐 Web Search**: Smithery API + MCP Protocol
- **🖥️ UI Framework**: Streamlit
- **🐍 Backend**: Python 3.10+
- **⚡ Async**: AsyncIO ile paralel işlem

## 📁 Proje Yapısı

```
mini-microcozmos/
├── src/
│   ├── personas/          # JSON persona dosyaları
│   ├── ui/               # Streamlit arayüzü
│   └── agents/           # Agent sınıfları
├── config/               # Konfigürasyon dosyaları
├── static/css/           # CSS stilleri
├── app.py               # Ana uygulama
└── requirements.txt     # Python bağımlılıkları
```

## 🌐 API Gereksinimleri

### Zorunlu:
- **Gemini API**: Ana LLM modeli için
  - [Google AI Studio](https://aistudio.google.com/)dan alın

### Opsiyonel:
- **Smithery API**: Web arama için
  - Olmadan da çalışır, sadece güncel bilgi alamaz

## ⚙️ Konfigürasyon

### Environment Variables:
```env
# Ana API (zorunlu)
GEMINI_API_KEY=your_key_here

# Web arama (opsiyonel)
SMITHERY_API_KEY=your_key
SMITHERY_PROFILE=your_profile

# Alternatif API'lar (opsiyonel)
GROQ_API_KEY=your_groq_key
OPENAI_API_KEY=your_openai_key
```

### Streamlit Config:
```toml
[server]
port = 8501
enableCORS = false

[theme]
primaryColor = "#667eea"
backgroundColor = "#f0f2f5"
```

## 🧪 Test Edilen Senaryolar

✅ **Güncel siyasi sorular** - Web araması ile güncel bilgi  
✅ **Ekonomi tartışmaları** - Persona bazlı görüş farklılıkları  
✅ **Sosyal konular** - Karakter tutarlılığı  
✅ **Paralel sohbet** - İki persona aynı anda  
✅ **API rotasyonu** - Quota aşımında otomatik geçiş  

## 🚨 Bilinen Sınırlamalar

- Web arama Smithery API'ya bağımlı
- Gemini API quota limitli
- Sadece Türkçe optimize edilmiş
- Persona'lar gerçek kişileri temsil etmez

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun: `git checkout -b feature/amazing-feature`
3. Commit yapın: `git commit -m 'Add amazing feature'`
4. Push edin: `git push origin feature/amazing-feature`
5. Pull Request açın

## 📄 Lisans

Bu proje MIT Lisansı altında lisanslanmıştır.

## ⚠️ Uyarılar

- Bu proje **araştırma ve eğitim** amaçlıdır
- Persona'lar **gerçek kişileri temsil etmez**
- AI yanıtları **bilimsel referans değildir**
- API kullanım limitlerini kontrol edin

## 🆘 Sorun Giderme

### Uygulama başlamıyor:
```bash
pip install --upgrade streamlit
streamlit run src/ui/streamlit_app_groq.py
```

### API hatası:
- `config/.env` dosyasını kontrol edin
- API key'lerin geçerli olduğundan emin olun
- Quota limitlerini kontrol edin

### Persona yüklenmiyor:
- `src/personas/` klasörünü kontrol edin
- JSON syntax hatalarını kontrol edin

## 📞 İletişim

- **Issues**: GitHub Issues kullanın
- **Discussions**: GitHub Discussions
- **Email**: [proje maintainer email]

---

**🎭 Mini Microcosmos** - Sequential Thinking ile güvenli AI persona simülasyonu