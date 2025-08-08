# 🎭 Mini Microcosmos - AI Persona Simulator

Türkiye'deki kararsız-küskün seçmen profillerini AI ajanları ile simüle eden proje.

## 📋 Özellikler

- **Persona Tabanlı Sohbet**: Farklı seçmen profillerinde AI ajanları
- **Sequential Thinking**: Gemini tabanlı düşünme mimarisi  
- **Web Arama Entegrasyonu**: Güncel bilgilere erişim
- **Gündem Özetleme**: Otomatik haber analizi
- **Çoklu API Desteği**: Quota aşımında otomatik geçiş

## 🚀 Kurulum

1. **Repo'yu klonlayın**:
```bash
git clone https://github.com/username/mini-microcozmos.git
cd mini-microcozmos
```

2. **Virtual environment oluşturun**:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# veya
.venv\Scripts\activate     # Windows
```

3. **Gereksinimleri yükleyin**:
```bash
pip install -r requirements.txt
```

4. **Çevre değişkenlerini ayarlayın**:
```bash
cp .env.example .env
# .env dosyasını düzenleyin ve API keylerini ekleyin
```

## 🔧 Konfigürasyon

### API Keys

#### Gemini API Keys
- [Google AI Studio](https://aistudio.google.com/)dan API key alın
- Birden fazla key ekleyebilirsiniz (quota aşımında otomatik geçiş)

#### Smithery API (Web Arama)
- Web arama fonksiyonları için gerekli
- `SMITHERY_API_KEY` ve `SMITHERY_PROFILE` ayarlayın

## 📱 Kullanım

```bash
python main.py
```

### Komutlar
- Normal sohbet için herhangi bir mesaj yazın
- `switch` - Manuel API key değiştir
- `quit` / `exit` - Çıkış

## 👥 Persona'lar

### Mevcut Persona'lar:
- **Tuğrul Bey**: 40'lı yaşlarda, milliyetçi, esnaf
- **Hatice Teyze**: 61 yaşında, muhafazakar, ev hanımı  
- **Elif**: 23 yaşında, üniversite öğrencisi, feminist
- **Kenan Bey**: 36 yaşında, Kemalist, eğitimli

### Persona Yapısı:
```json
{
  "name": "Persona Adı",
  "bio": ["Temel bilgiler..."],
  "lore": ["Detaylı geçmiş..."],
  "knowledge": ["Bilgi kaynakları..."],
  "style": {
    "chat": ["Konuşma tarzı..."],
    "post": ["Paylaşım tarzı..."]
  }
}
```

## 🏗️ Mimari

### Sequential Thinking Pipeline:
1. **Soru Analizi**: Kullanıcı sorgusunu çözümle
2. **Arama Kararı**: Web araması gerekli mi?
3. **Arama Terimleri**: En uygun anahtar kelimeler
4. **Gündem Özetleme**: Haber sonuçlarını özetle
5. **Cevap Planlama**: Response stratejisini belirle
6. **Final Cevap**: Persona karakterinde yanıtla

### Teknolojiler:
- **Google Gemini**: Ana LLM motoru
- **MCP Protocol**: Web arama entegrasyonu  
- **Smithery API**: Güncel haber kaynakları
- **Async Python**: Performanslı I/O işlemleri

## 📊 Özellik Detayları

### Web Arama
- Çoklu arama stratejisi
- Site analizi ve doğrulama
- Tarih kontrolü (Temmuz 2025 odaklı)
- Otomatik gündem özetleme

### AI Ajanları  
- Persona tabanlı kimlik
- Bilinçaltı siyasi hafıza
- Gerçekçi konuşma tarzları
- Güncel olay yorumlama

### Güvenlik
- API key rotasyonu
- Encoding güvenliği (UTF-8)
- Hata toleransı
- Quota yönetimi

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişiklikleri commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'i push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır.

## ⚠️ Uyarılar

- Bu proje araştırma ve eğitim amaçlıdır
- Persona'lar gerçek kişileri temsil etmez
- AI yanıtları bilimsel referans değildir
- API kullanım limitlerini kontrol edin# mini-microcosmoz
