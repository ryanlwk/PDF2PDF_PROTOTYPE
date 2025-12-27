import os
import requests

def download_file(url, save_path):
    """Download a file from URL to save_path."""
    print(f"⬇️  Downloading {os.path.basename(save_path)}...")
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        file_size_mb = os.path.getsize(save_path) / (1024 * 1024)
        print(f"✅ Saved to {save_path} ({file_size_mb:.1f} MB)")
        return True
    except Exception as e:
        print(f"❌ Failed to download: {e}")
        return False

def main():
    """Download all required Traditional Chinese fonts for PDF rendering."""
    font_dir = "fonts"
    
    # Create fonts directory if it doesn't exist
    if not os.path.exists(font_dir):
        os.makedirs(font_dir)
        print(f"📁 Created directory: {font_dir}/")
    
    print("=" * 60)
    print("🔤 Font Downloader - Traditional Chinese Support")
    print("=" * 60)
    print()
    
    # Define font URLs
    fonts = {
        "NotoSansCJKtc-Regular.otf": "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/TraditionalChinese/NotoSansCJKtc-Regular.otf",
        "NotoSansCJKtc-Bold.otf": "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/TraditionalChinese/NotoSansCJKtc-Bold.otf",
        "NotoSerifCJKtc-Regular.otf": "https://github.com/notofonts/noto-cjk/raw/main/Serif/OTF/TraditionalChinese/NotoSerifCJKtc-Regular.otf"
    }
    
    downloaded = 0
    skipped = 0
    failed = 0
    
    for filename, url in fonts.items():
        path = os.path.join(font_dir, filename)
        
        if os.path.exists(path):
            print(f"👌 {filename} already exists. Skipping...")
            skipped += 1
        else:
            if download_file(url, path):
                downloaded += 1
            else:
                failed += 1
        print()
    
    print("=" * 60)
    print("📊 Download Summary:")
    print(f"   ✅ Downloaded: {downloaded}")
    print(f"   ⏭️  Skipped: {skipped}")
    if failed > 0:
        print(f"   ❌ Failed: {failed}")
    print("=" * 60)
    print()
    
    if failed == 0:
        print("✅ All fonts ready!")
        print("👉 Next step: python tools/extract_il_v2.py")
    else:
        print("⚠️  Some fonts failed to download. Please check your internet connection.")

if __name__ == "__main__":
    main()
