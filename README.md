# 🎭 Mini Microcosmos - AI Persona Simulator

Sequential Thinking mimarisi ile AI persona simülasyonu.

## 🚀 Hızlı Başlangıç

### 1. Kurulum
```bash
git clone <repo-url>
cd mini-microcozmos
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. API Keys
```bash
cp config/.env.example config/.env
# config/.env dosyasına 14 Gemini API key ekleyin
```

### 3. Çalıştırma
```bash
# Yöntem 1 (Önerilen)
python run_app.py

# Yöntem 2 (Direkt)
streamlit run src/ui/streamlit_app_groq.py
```

## ✨ Özellikler

- 🧠 Sequential Thinking (7 aşama)
- 🔄 14 Gemini API key otomatik rotasyon
- 🎭 İki persona paralel çalışma
- 🌙 Black theme arayüz
- 🔍 Web arama (opsiyonel)

## 🎯 Persona'lar

- **🎯 Eski Tuğrul**: MHP/Ülkücü
- **🔄 Yeni Tuğrul**: CHP'ye geçiş

## 📁 Proje Yapısı
```
mini-microcozmos/
├── src/
│   ├── personas/         # JSON persona dosyaları
│   ├── ui/              # Streamlit arayüzü
│   └── agents/          # Agent sınıfları
├── config/              # Konfigürasyon
├── .streamlit/          # Streamlit config
├── run_app.py          # Ana başlatıcı
└── requirements.txt    # Bağımlılıklar
```

## 🔧 Sorun Giderme

**Uygulama başlamıyor:**
```bash
pip install --upgrade streamlit
python run_app.py
```

**API hatası:**
- config/.env'de 14 Gemini key'i kontrol edin
- API quota'larını kontrol edin

---
🎭 **Mini Microcosmos** - Sequential Thinking AI
