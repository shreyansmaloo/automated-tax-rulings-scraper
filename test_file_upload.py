import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.file_upload import upload_and_cleanup


def test_file_upload():
    """Test FTP file upload and cleanup functionality"""
    print("🧪 Testing FTP file upload and cleanup...")
    try:
        upload_and_cleanup()
        print("✅ FTP upload and cleanup completed successfully.")
        return True
    except Exception as e:
        print(f"❌ FTP upload and cleanup failed: {e}")
        return False

if __name__ == "__main__":
    test_file_upload()
