#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mini Microcosmos - Ana Başlatma Script
Optimize edilmiş versiyon - Terminal: python run_app.py
"""

import subprocess
import sys
import os
from pathlib import Path


def check_requirements():
    """Gereksinimleri kontrol et"""
    print("🔍 Gereksinimler kontrol ediliyor...")

    # .env dosyası kontrolü
    if not os.path.exists('config/.env'):
        print("❌ config/.env dosyası bulunamadı!")
        print("💡 config/.env.example'ı kopyalayıp API keylerini ekleyin")
        return False

    # Persona dosyaları kontrolü
    persona_files = [
        'src/personas/tugrul_eski.json',
        'src/personas/tugrul_yeni.json'
    ]

    missing_personas = []
    for persona in persona_files:
        if not os.path.exists(persona):
            missing_personas.append(persona)

    if missing_personas:
        print(f"❌ Eksik persona dosyaları: {missing_personas}")
        return False

    # Ana uygulama dosyası kontrolü
    if not os.path.exists('src/ui/app.py'):
        print("❌ Ana uygulama dosyası bulunamadı: src/ui/app.py")
        return False

    print("✅ Tüm gereksinimler tamam!")
    return True


def check_api_keys():
    """API key'lerini kontrol et"""
    from dotenv import load_dotenv
    load_dotenv(dotenv_path='config/.env')

    # Gemini API kontrolü
    gemini_keys = []
    main_key = os.getenv("GEMINI_API_KEY")
    if main_key:
        gemini_keys.append(main_key)

    # Çoklu API key kontrolü
    for i in range(1, 15):
        key = os.getenv(f"GEMINI_API_KEY_{i}")
        if key:
            gemini_keys.append(key)

    if not gemini_keys:
        print("❌ GEMINI_API_KEY bulunamadı!")
        print("💡 config/.env dosyasına en az bir GEMINI_API_KEY ekleyin")
        return False

    print(f"✅ {len(gemini_keys)} Gemini API Key bulundu")

    # Smithery API (opsiyonel)
    smithery_key = os.getenv("SMITHERY_API_KEY")
    if smithery_key:
        print("✅ Smithery API Key bulundu (Web arama aktif)")
    else:
        print("⚠️ Smithery API Key yok (Web arama kapalı)")

    return True


def main():
    """Ana fonksiyon"""
    print("🎭 Mini Microcosmos - AI Persona Simulator")
    print("=" * 50)
    print("🧠 Sequential Thinking mimarisi ile güvenli persona simülasyonu")
    print("=" * 50)

    # Gereksinim kontrolü
    if not check_requirements():
        print("\n🔧 Eksiklikleri giderdikten sonra tekrar deneyin:")
        print("1. config/.env dosyasını oluşturun")
        print("2. GEMINI_API_KEY=your_key_here ekleyin")
        print("3. Persona dosyalarının varlığını kontrol edin")
        return

    # API key kontrolü
    if not check_api_keys():
        print("\n🔧 API key ayarlarını yapın:")
        print("1. https://aistudio.google.com/ adresinden Gemini API key alın")
        print("2. config/.env dosyasına GEMINI_API_KEY=your_key ekleyin")
        return

    # Streamlit'i başlat
    print("\n🚀 Streamlit uygulaması başlatılıyor...")
    print("🌐 Tarayıcınızda http://localhost:8501 açılacak")
    print("⏹️ Durdurmak için Ctrl+C basın")
    print("-" * 50)

    try:
        # Optimize edilmiş path ile başlat
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "src/ui/app.py",
            "--server.port=8501",
            "--server.headless=false",
            "--server.enableCORS=false",
            "--server.enableXsrfProtection=false"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 Uygulama güvenli şekilde kapatıldı.")
        print("🎭 Mini Microcosmos'u kullandığınız için teşekkürler!")
    except Exception as e:
        print(f"\n❌ Beklenmeyen hata: {e}")
        print("💡 Lütfen requirements.txt'i kontrol edin:")
        print("   pip install -r requirements.txt")


if __name__ == "__main__":
    main()