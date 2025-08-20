import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("✅ Requirements installed successfully")

def setup_playwright():
    """Setup Playwright browsers"""
    print("🎭 Setting up Playwright browsers...")
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    print("✅ Playwright browsers installed successfully")

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = [
        "scraped_bangladesh_news",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"  ✅ Created: {directory}")


def main():
    """Main setup function"""
    print("🚀 Bangladesh News Event Scraper Setup")
    print("="*50)
    
    try:
        install_requirements()
        setup_playwright()
        create_directories()
        
        print("\n✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Add your Google API key to the .env file")
        print("2. Prepare your CSV file with news events")
        print("3. Run: python run_scraper.py")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()