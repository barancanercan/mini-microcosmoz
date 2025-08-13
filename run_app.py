#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mini Microcosmos - Ana Başlatma Script
Terminal: python run_app.py
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
    
    # Persona dosyaları
    persona_files = [
        'src/personas/tugrul_bey.json',
        'src/personas/yeni_tugrul.json'
    ]
    
    missing_personas = []
    for persona in persona_files:
        if not os.path.exists(persona):
            missing_personas.append(persona)
    
    if missing_personas:
        print(f"❌ Eksik persona dosyaları: {missing_personas}")
        return False
    
    print("✅ Tüm gereksinimler tamam!")
    return True

def main():
    """Ana fonksiyon"""
    print("🎭 Mini Microcosmos Başlatılıyor...")
    print("=" * 40)
    
    if not check_requirements():
        print("\n🔧 Lütfen eksiklikleri giderin ve tekrar deneyin.")
        return
    
    # Streamlit'i başlat
    print("🚀 Streamlit başlatılıyor...")
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "src/ui/streamlit_app_groq.py",
            "--server.port=8501"
        ])
    except KeyboardInterrupt:
        print("\n👋 Uygulama kapatıldı.")
    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    main()
