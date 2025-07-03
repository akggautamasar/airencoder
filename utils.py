"""
Utility functions for the video encoder bot
"""
import os
import json
import subprocess
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

def format_file_size(size_bytes: int) -> str:
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"

def format_duration(seconds: float) -> str:
    """Convert seconds to human readable duration"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def get_video_info(file_path: str) -> Optional[Dict[str, Any]]:
    """Extract video information using ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            video_stream = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
            audio_stream = next((s for s in data['streams'] if s['codec_type'] == 'audio'), None)
            
            if video_stream:
                info = {
                    'duration': float(data['format'].get('duration', 0)),
                    'width': int(video_stream.get('width', 0)),
                    'height': int(video_stream.get('height', 0)),
                    'video_codec': video_stream.get('codec_name', 'unknown'),
                    'bitrate': int(data['format'].get('bit_rate', 0)),
                    'fps': eval(video_stream.get('r_frame_rate', '0/1')) if video_stream.get('r_frame_rate') else 0,
                    'has_audio': audio_stream is not None
                }
                
                if audio_stream:
                    info['audio_codec'] = audio_stream.get('codec_name', 'unknown')
                    info['audio_bitrate'] = int(audio_stream.get('bit_rate', 0))
                
                return info
                
    except Exception as e:
        logger.error(f"Error getting video info for {file_path}: {e}")
    
    return None

def validate_video_file(file_path: str) -> bool:
    """Validate if file is a valid video"""
    try:
        info = get_video_info(file_path)
        return info is not None and info.get('duration', 0) > 0
    except Exception:
        return False

def clean_filename(filename: str) -> str:
    """Clean filename for safe file operations"""
    import re
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple underscores
    filename = re.sub(r'_+', '_', filename)
    # Remove leading/trailing underscores and dots
    filename = filename.strip('_.')
    
    return filename or "video"

def estimate_processing_time(duration: float, resolution: str, quality: str) -> float:
    """Estimate processing time based on video properties"""
    # Base processing time (seconds per second of video)
    base_multiplier = {
        '240p': 0.5,
        '360p': 0.7,
        '480p': 1.0,
        '720p': 1.5,
        '1080p': 2.5
    }
    
    quality_multiplier = {
        'ultrafast': 0.3,
        'fast': 0.7,
        'medium': 1.0,
        'slow': 1.8,
        'veryslow': 3.0
    }
    
    base = base_multiplier.get(resolution, 1.0)
    quality_mult = quality_multiplier.get(quality, 1.0)
    
    return duration * base * quality_mult

def check_disk_space(required_bytes: int, path: str = ".") -> bool:
    """Check if there's enough disk space"""
    try:
        import shutil
        free_bytes = shutil.disk_usage(path).free
        return free_bytes > required_bytes * 2  # Require 2x space for safety
    except Exception:
        return True  # Assume OK if can't check

def get_optimal_threads() -> int:
    """Get optimal number of threads for encoding"""
    try:
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()
        # Use 75% of available cores, minimum 1, maximum 8
        return max(1, min(8, int(cpu_count * 0.75)))
    except Exception:
        return 2  # Safe default