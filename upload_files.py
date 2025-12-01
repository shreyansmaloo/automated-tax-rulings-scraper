import os
import sys
from ftplib import FTP, error_perm
from pathlib import Path
from dotenv import load_dotenv
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_environment():
    """Load environment variables and validate required ones."""
    load_dotenv()
    
    required_vars = [
        'FTP_HOST', 'FTP_USER', 'FTP_PASS', 
        'LOCAL_DIR', 'REMOTE_DIR'
    ]
    
    config = {var: os.getenv(var) for var in required_vars}
    
    # Validate required variables
    missing = [var for var, val in config.items() if not val]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    # Set default port if not specified
    config['FTP_PORT'] = int(os.getenv('FTP_PORT', '21'))
    
    # Ensure local directory exists
    local_dir = Path(config['LOCAL_DIR']).expanduser().resolve()
    if not local_dir.exists():
        logger.info(f"Creating local directory: {local_dir}")
        local_dir.mkdir(parents=True, exist_ok=True)
    config['LOCAL_DIR'] = local_dir
    
    return config

def ensure_remote_dir(ftp, remote_path):
    """Ensure remote directory exists, create if it doesn't."""
    try:
        ftp.cwd(remote_path)
    except error_perm as e:
        if "550" in str(e):  # Directory doesn't exist
            logger.info(f"Creating remote directory: {remote_path}")
            try:
                # Try to create the directory
                ftp.mkd(remote_path)
                logger.info(f"Created remote directory: {remote_path}")
            except error_perm as e:
                logger.error(f"Failed to create remote directory: {e}")
                raise
            ftp.cwd(remote_path)
        else:
            raise

def upload_file(ftp, local_path, remote_path):
    """Upload a single file to the FTP server."""
    try:
        with open(local_path, 'rb') as f:
            ftp.storbinary(f'STOR {remote_path}', f)
        logger.info(f"Uploaded: {local_path} -> {remote_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to upload {local_path}: {str(e)}")
        return False

def main():
    try:
        # Load and validate configuration
        config = load_environment()
        
        logger.info("Starting FTP upload process...")
        logger.info(f"Local directory: {config['LOCAL_DIR']}")
        logger.info(f"Remote directory: {config['REMOTE_DIR']}")
        
        # Connect to FTP server
        ftp = FTP()
        ftp.connect(config['FTP_HOST'], config['FTP_PORT'], timeout=30)
        logger.info(f"Connected to {config['FTP_HOST']}:{config['FTP_PORT']}")
        
        # Login
        ftp.login(config['FTP_USER'], config['FTP_PASS'])
        logger.info("Successfully logged in")
        
        # Ensure remote directory exists
        ensure_remote_dir(ftp, config['REMOTE_DIR'])
        
        # Get list of files to upload
        files_to_upload = [
            f for f in config['LOCAL_DIR'].iterdir() 
            if f.is_file() and not f.name.startswith('.')
        ]
        
        if not files_to_upload:
            logger.info("No files found to upload")
            return
        
        logger.info(f"Found {len(files_to_upload)} file(s) to upload")
        
        # Upload files
        success_count = 0
        for file_path in files_to_upload:
            remote_path = file_path.name
            if upload_file(ftp, str(file_path), remote_path):
                success_count += 1
                # Optionally delete the file after successful upload
                try:
                    file_path.unlink()
                    logger.info(f"Deleted local file: {file_path}")
                except Exception as e:
                    logger.warning(f"Could not delete {file_path}: {str(e)}")
        
        logger.info(f"Upload complete. {success_count}/{len(files_to_upload)} files uploaded successfully")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        try:
            ftp.quit()
            logger.info("FTP connection closed")
        except:
            pass

if __name__ == "__main__":
    main()