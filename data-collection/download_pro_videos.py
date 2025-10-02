import yt_dlp
import os
import logging
import shutil

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_pro_video(url, output_path):
    """Download a specific pro video from YouTube"""
    logger.info(f"Downloading video from {url} to {output_path}")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    ydl_opts = {
        'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        'outtmpl': output_path,
        'quiet': False,
        'no_warnings': False
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        logger.info(f"Download completed successfully to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        return False

if __name__ == "__main__":
    # First, check if pro_videos exists and handle it
    if os.path.exists("pro_videos"):
        if not os.path.isdir("pro_videos"):
            # If it exists but is not a directory, rename it
            logger.warning("pro_videos exists but is not a directory. Renaming it.")
            os.rename("pro_videos", "pro_videos_old")
            os.mkdir("pro_videos")
    else:
        # If it doesn't exist, create it
        os.mkdir("pro_videos")
    
    # Now create the mcbeth directory
    mcbeth_dir = "pro_videos/mcbeth"
    if os.path.exists(mcbeth_dir):
        if not os.path.isdir(mcbeth_dir):
            os.rename(mcbeth_dir, f"{mcbeth_dir}_old")
            os.mkdir(mcbeth_dir)
    else:
        os.mkdir(mcbeth_dir)
    
    # Finally create the backhand directory
    backhand_dir = f"{mcbeth_dir}/backhand"
    if os.path.exists(backhand_dir):
        if not os.path.isdir(backhand_dir):
            os.rename(backhand_dir, f"{backhand_dir}_old")
            os.mkdir(backhand_dir)
    else:
        os.mkdir(backhand_dir)
    
    # Download Paul McBeth backhand videos
    download_pro_video(
        "https://www.youtube.com/watch?v=Vn9_Pjp8iHY",
        "pro_videos/mcbeth/backhand/mcbeth_backhand_slow_1.mp4"
    )
    
    download_pro_video(
        "https://www.youtube.com/watch?v=sPrUjSKpPD0",
        "pro_videos/mcbeth/backhand/mcbeth_backhand_slow_2.mp4"
    )