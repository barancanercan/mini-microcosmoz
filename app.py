#!/usr/bin/env python3
"""
Mini Microcosmos - Groq API Runner
Fixed version for Streamlit with Groq API
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))


def check_groq_requirements():
    """Check if Groq requirements are met"""
    required_files = [
        'src/ui/streamlit_app_groq.py',
        'src/personas/tugrul_bey.json',
        'src/personas/yeni_tugrul.json',
        'config/.env'
    ]

    missing_files = []
    for file_path in required_files:
        if not (project_root / file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print("❌ Eksik dosyalar:")
        for file in missing_files:
            print(f"   - {file}")
        return False

    # Check Groq API key
    from dotenv import load_dotenv
    load_dotenv(dotenv_path='config/.env')

    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("❌ GROQ_API_KEY bulunamadı!")
        print("💡 config/.env dosyasına GROQ_API_KEY=your_key_here ekleyin")
        return False

    print(f"✅ Groq API Key: {groq_key[:10]}...{groq_key[-4:]}")
    return True


def main():
    """Main application entry point"""
    print("🎭 Mini Microcosmos - Groq API Version")
    print("=====================================")

    # Check requirements
    if not check_groq_requirements():
        print("\n🔧 Eksik gereksinimleri tamamlayın:")
        print("1. config/.env dosyasını oluşturun")
        print("2. GROQ_API_KEY=your_groq_api_key_here ekleyin")
        print("3. Groq API key'i https://console.groq.com/keys adresinden alın")
        sys.exit(1)

    print("✅ Tüm gereksinimler karşılandı")
    print("🚀 Streamlit uygulaması başlatılıyor...")

    # Import and run the Streamlit app
    try:
        from ui.streamlit_app_groq import main as streamlit_main
        streamlit_main()
    except ImportError as e:
        print(f"❌ Import hatası: {e}")
        print("💡 src/ui/streamlit_app_groq.py dosyasını kontrol edin")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Uygulama hatası: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()