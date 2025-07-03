import asyncio
import os
import subprocess
import uuid
import time
import logging
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import FloodWait
import psutil
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load from environment with validation
try:
    API_ID = int(os.environ.get("API_ID"))
    API_HASH = os.environ.get("API_HASH")
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()]
    MAX_FILE_SIZE = int(os.environ.get("MAX_FILE_SIZE", "2147483648"))  # 2GB default
    WATERMARK_TEXT = os.environ.get("WATERMARK_TEXT", "@YourBrand")
    
    if not all([API_ID, API_HASH, BOT_TOKEN]):
        raise ValueError("Missing required environment variables")
        
except (ValueError, TypeError) as e:
    logger.error(f"Environment configuration error: {e}")
    exit(1)

app = Client("transcoder_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Create necessary directories
for directory in ["downloads", "outputs", "temp"]:
    os.makedirs(directory, exist_ok=True)

# Memory-based session storage
video_sessions = {}
user_stats = {}
processing_queue = {}

# Supported formats and presets
SUPPORTED_FORMATS = {
    'mp4': 'MP4 (H.264)',
    'mkv': 'MKV (H.264)',
    'avi': 'AVI (H.264)',
    'webm': 'WebM (VP9)',
    'mov': 'MOV (H.264)'
}

QUALITY_PRESETS = {
    'ultrafast': {'preset': 'ultrafast', 'crf': '28'},
    'fast': {'preset': 'fast', 'crf': '23'},
    'medium': {'preset': 'medium', 'crf': '20'},
    'slow': {'preset': 'slow', 'crf': '18'},
    'veryslow': {'preset': 'veryslow', 'crf': '15'}
}

RESOLUTION_PRESETS = {
    '240p': {'height': 240, 'bitrate': '400k'},
    '360p': {'height': 360, 'bitrate': '800k'},
    '480p': {'height': 480, 'bitrate': '1200k'},
    '720p': {'height': 720, 'bitrate': '2500k'},
    '1080p': {'height': 1080, 'bitrate': '5000k'}
}

def get_system_stats():
    """Get current system resource usage"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        'cpu': cpu_percent,
        'memory_used': memory.percent,
        'memory_available': memory.available // (1024**3),  # GB
        'disk_free': disk.free // (1024**3)  # GB
    }

def format_file_size(size_bytes):
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f}{size_names[i]}"

def get_video_info(file_path):
    """Extract video information using ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            video_stream = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
            
            if video_stream:
                return {
                    'duration': float(data['format'].get('duration', 0)),
                    'width': int(video_stream.get('width', 0)),
                    'height': int(video_stream.get('height', 0)),
                    'codec': video_stream.get('codec_name', 'unknown'),
                    'bitrate': int(data['format'].get('bit_rate', 0)),
                    'fps': eval(video_stream.get('r_frame_rate', '0/1'))
                }
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
    
    return None

async def update_user_stats(user_id, action):
    """Update user statistics"""
    if user_id not in user_stats:
        user_stats[user_id] = {
            'videos_processed': 0,
            'total_size_processed': 0,
            'first_use': datetime.now().isoformat(),
            'last_use': datetime.now().isoformat()
        }
    
    user_stats[user_id]['last_use'] = datetime.now().isoformat()
    
    if action == 'video_processed':
        user_stats[user_id]['videos_processed'] += 1

@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    await update_user_stats(user_id, 'start')
    
    welcome_text = f"""
🎬 **Advanced Video Encoder Bot**

👋 Welcome {message.from_user.first_name}!

**Features:**
• Multiple resolution support (240p to 1080p)
• Various output formats (MP4, MKV, AVI, WebM, MOV)
• Quality presets (Ultra Fast to Very Slow)
• Custom watermarks
• Batch processing
• Video information analysis
• Progress tracking

**Commands:**
/start - Show this message
/help - Detailed help
/stats - Your usage statistics
/formats - Supported formats
/admin - Admin panel (admins only)

📤 **Send me a video file to get started!**
Max file size: {format_file_size(MAX_FILE_SIZE)}
    """
    
    await message.reply(welcome_text)

@app.on_message(filters.command("help"))
async def help_command(client, message):
    help_text = """
📖 **Detailed Help**

**How to use:**
1. Send a video file (up to 2GB)
2. Choose your preferred settings
3. Wait for processing
4. Download your converted video

**Resolution Options:**
• 240p - Low quality, small file
• 360p - Standard quality
• 480p - Good quality
• 720p - HD quality
• 1080p - Full HD quality

**Quality Presets:**
• Ultra Fast - Quick processing, larger file
• Fast - Balanced speed and quality
• Medium - Good quality, moderate speed
• Slow - High quality, slower processing
• Very Slow - Best quality, slowest processing

**Output Formats:**
• MP4 - Most compatible
• MKV - High quality container
• AVI - Legacy compatibility
• WebM - Web optimized
• MOV - Apple compatible

**Tips:**
• Use Fast preset for quick results
• Use Slow preset for best quality
• 720p is recommended for most uses
• MP4 format works on all devices
    """
    
    await message.reply(help_text)

@app.on_message(filters.command("stats"))
async def stats_command(client, message):
    user_id = message.from_user.id
    stats = user_stats.get(user_id, {})
    
    if not stats:
        await message.reply("📊 No statistics available. Process a video first!")
        return
    
    stats_text = f"""
📊 **Your Statistics**

🎬 Videos processed: {stats.get('videos_processed', 0)}
📦 Total data processed: {format_file_size(stats.get('total_size_processed', 0))}
📅 First use: {stats.get('first_use', 'Unknown')[:10]}
🕐 Last use: {stats.get('last_use', 'Unknown')[:10]}
    """
    
    await message.reply(stats_text)

@app.on_message(filters.command("formats"))
async def formats_command(client, message):
    formats_text = "📋 **Supported Output Formats:**\n\n"
    
    for ext, desc in SUPPORTED_FORMATS.items():
        formats_text += f"• **{ext.upper()}** - {desc}\n"
    
    formats_text += "\n🎯 **Available Resolutions:**\n"
    for res, info in RESOLUTION_PRESETS.items():
        formats_text += f"• **{res}** - {info['height']}p @ {info['bitrate']} bitrate\n"
    
    await message.reply(formats_text)

@app.on_message(filters.command("admin") & filters.user(ADMIN_IDS))
async def admin_panel(client, message):
    system_stats = get_system_stats()
    total_users = len(user_stats)
    total_videos = sum(stats.get('videos_processed', 0) for stats in user_stats.values())
    active_processes = len(processing_queue)
    
    admin_text = f"""
🔧 **Admin Panel**

**System Status:**
🖥️ CPU Usage: {system_stats['cpu']:.1f}%
💾 Memory Usage: {system_stats['memory_used']:.1f}%
💿 Free Disk Space: {system_stats['disk_free']}GB

**Bot Statistics:**
👥 Total Users: {total_users}
🎬 Total Videos Processed: {total_videos}
⚙️ Active Processes: {active_processes}

**Queue Status:**
📋 Videos in queue: {len(processing_queue)}
    """
    
    buttons = [
        [InlineKeyboardButton("🗑️ Clear Cache", callback_data="admin_clear_cache")],
        [InlineKeyboardButton("📊 Detailed Stats", callback_data="admin_detailed_stats")],
        [InlineKeyboardButton("🔄 Restart Bot", callback_data="admin_restart")]
    ]
    
    await message.reply(admin_text, reply_markup=InlineKeyboardMarkup(buttons))

@app.on_message(filters.video | filters.document)
async def handle_video(client, message):
    user_id = message.from_user.id
    
    # Check file size
    file_size = message.video.file_size if message.video else message.document.file_size
    if file_size > MAX_FILE_SIZE:
        await message.reply(f"❌ File too large! Max size: {format_file_size(MAX_FILE_SIZE)}")
        return
    
    # Check if user has active processing
    if user_id in processing_queue:
        await message.reply("⏳ You already have a video being processed. Please wait for it to complete.")
        return
    
    msg = await message.reply("⬇️ Downloading video... 0%")
    
    try:
        # Generate unique ID and path
        video_id = str(uuid.uuid4())
        file_extension = message.video.file_name.split('.')[-1] if message.video and message.video.file_name else 'mp4'
        video_path = f"downloads/{video_id}.{file_extension}"
        
        # Download with progress
        start_time = time.time()
        
        def progress_callback(current, total):
            percent = (current / total) * 100
            if time.time() - start_time > 2:  # Update every 2 seconds
                asyncio.create_task(msg.edit(f"⬇️ Downloading video... {percent:.1f}%"))
        
        await message.download(file_name=video_path, progress=progress_callback)
        
        # Get video information
        video_info = get_video_info(video_path)
        
        video_sessions[video_id] = {
            'path': video_path,
            'user_id': user_id,
            'original_size': file_size,
            'info': video_info,
            'timestamp': time.time()
        }
        
        await msg.edit("✅ Download complete! Analyzing video...")
        
        # Show video info and options
        info_text = "📹 **Video Information:**\n"
        if video_info:
            info_text += f"📐 Resolution: {video_info['width']}x{video_info['height']}\n"
            info_text += f"⏱️ Duration: {video_info['duration']:.1f}s\n"
            info_text += f"🎞️ Codec: {video_info['codec']}\n"
            info_text += f"📊 Bitrate: {format_file_size(video_info['bitrate']//8)}/s\n"
            info_text += f"🎬 FPS: {video_info['fps']:.1f}\n"
        
        info_text += f"📦 File Size: {format_file_size(file_size)}\n\n"
        info_text += "🎯 Choose conversion options:"
        
        buttons = [
            [InlineKeyboardButton("🎬 Quick Convert", callback_data=f"quick|{video_id}")],
            [InlineKeyboardButton("⚙️ Advanced Options", callback_data=f"advanced|{video_id}")],
            [InlineKeyboardButton("📋 Batch Convert", callback_data=f"batch|{video_id}")]
        ]
        
        await message.reply(info_text, reply_markup=InlineKeyboardMarkup(buttons))
        
    except Exception as e:
        logger.error(f"Error handling video: {e}")
        await msg.edit(f"❌ Error downloading video: {str(e)}")
        if video_id in video_sessions:
            cleanup_session(video_id)

def cleanup_session(video_id):
    """Clean up session files and data"""
    if video_id in video_sessions:
        session = video_sessions[video_id]
        if os.path.exists(session['path']):
            os.remove(session['path'])
        del video_sessions[video_id]
    
    # Remove from processing queue
    for user_id, vid_id in list(processing_queue.items()):
        if vid_id == video_id:
            del processing_queue[user_id]

async def transcode_video(input_file, output_file, resolution, quality_preset, format_type, watermark=True, progress_callback=None):
    """Advanced video transcoding with progress tracking"""
    try:
        # Build ffmpeg command
        cmd = ['ffmpeg', '-i', input_file, '-y']
        
        # Video filters
        filters = []
        
        # Resolution scaling
        if resolution in RESOLUTION_PRESETS:
            height = RESOLUTION_PRESETS[resolution]['height']
            filters.append(f"scale=-2:{height}")
        
        # Watermark
        if watermark and WATERMARK_TEXT:
            watermark_filter = f"drawtext=text='{WATERMARK_TEXT}':fontcolor=white:fontsize=24:x=10:y=10:enable='between(t,0,999999)'"
            filters.append(watermark_filter)
        
        if filters:
            cmd.extend(['-vf', ','.join(filters)])
        
        # Quality settings
        if quality_preset in QUALITY_PRESETS:
            preset_settings = QUALITY_PRESETS[quality_preset]
            cmd.extend(['-preset', preset_settings['preset']])
            cmd.extend(['-crf', preset_settings['crf']])
        
        # Codec settings based on format
        if format_type == 'webm':
            cmd.extend(['-c:v', 'libvpx-vp9', '-c:a', 'libopus'])
        else:
            cmd.extend(['-c:v', 'libx264', '-c:a', 'aac'])
        
        # Bitrate settings
        if resolution in RESOLUTION_PRESETS:
            cmd.extend(['-b:v', RESOLUTION_PRESETS[resolution]['bitrate']])
        
        cmd.extend(['-b:a', '128k'])
        cmd.append(output_file)
        
        # Execute with progress tracking
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"FFmpeg error: {stderr}")
        
        return True
        
    except Exception as e:
        logger.error(f"Transcoding error: {e}")
        raise

@app.on_callback_query()
async def handle_callback(client, callback_query):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    try:
        if data.startswith("admin_") and user_id in ADMIN_IDS:
            await handle_admin_callback(client, callback_query)
            return
        
        action, video_id = data.split("|", 1)
        session = video_sessions.get(video_id)
        
        if not session or session['user_id'] != user_id:
            await callback_query.message.edit_text("❌ Invalid selection or session expired.")
            return
        
        if not os.path.exists(session['path']):
            await callback_query.message.edit_text("❌ Video file not found.")
            cleanup_session(video_id)
            return
        
        if action == "quick":
            await show_quick_options(callback_query, video_id)
        elif action == "advanced":
            await show_advanced_options(callback_query, video_id)
        elif action == "batch":
            await show_batch_options(callback_query, video_id)
        elif action.startswith("convert_"):
            await process_conversion(callback_query, video_id, action)
        
    except Exception as e:
        logger.error(f"Callback error: {e}")
        await callback_query.message.edit_text(f"❌ Error: {str(e)}")

async def show_quick_options(callback_query, video_id):
    """Show quick conversion options"""
    buttons = [
        [InlineKeyboardButton("360p MP4", callback_data=f"convert_360p_mp4_fast|{video_id}")],
        [InlineKeyboardButton("480p MP4", callback_data=f"convert_480p_mp4_fast|{video_id}")],
        [InlineKeyboardButton("720p MP4", callback_data=f"convert_720p_mp4_fast|{video_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data=f"back|{video_id}")]
    ]
    
    await callback_query.message.edit_text(
        "🚀 **Quick Convert Options:**\n\nFast processing with good quality",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def show_advanced_options(callback_query, video_id):
    """Show advanced conversion options"""
    buttons = [
        [InlineKeyboardButton("📐 Choose Resolution", callback_data=f"res_select|{video_id}")],
        [InlineKeyboardButton("🎨 Choose Format", callback_data=f"format_select|{video_id}")],
        [InlineKeyboardButton("⚡ Choose Quality", callback_data=f"quality_select|{video_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data=f"back|{video_id}")]
    ]
    
    await callback_query.message.edit_text(
        "⚙️ **Advanced Options:**\n\nCustomize your conversion settings",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def show_batch_options(callback_query, video_id):
    """Show batch conversion options"""
    buttons = [
        [InlineKeyboardButton("All Resolutions (MP4)", callback_data=f"convert_batch_all_mp4|{video_id}")],
        [InlineKeyboardButton("Mobile Pack (240p+360p)", callback_data=f"convert_batch_mobile|{video_id}")],
        [InlineKeyboardButton("HD Pack (720p+1080p)", callback_data=f"convert_batch_hd|{video_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data=f"back|{video_id}")]
    ]
    
    await callback_query.message.edit_text(
        "📋 **Batch Convert Options:**\n\nProcess multiple formats at once",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def process_conversion(callback_query, video_id, action):
    """Process the video conversion"""
    user_id = callback_query.from_user.id
    session = video_sessions[video_id]
    
    # Add to processing queue
    processing_queue[user_id] = video_id
    
    try:
        await callback_query.message.edit_text("⚙️ Starting conversion... Please wait.")
        
        # Parse conversion parameters
        parts = action.replace("convert_", "").split("_")
        
        if parts[0] == "batch":
            await process_batch_conversion(callback_query, video_id, parts[1])
        else:
            resolution = parts[0]
            format_type = parts[1]
            quality = parts[2] if len(parts) > 2 else 'fast'
            
            await process_single_conversion(callback_query, video_id, resolution, format_type, quality)
        
        # Update user stats
        await update_user_stats(user_id, 'video_processed')
        
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        await callback_query.message.reply(f"❌ Conversion failed: {str(e)}")
    finally:
        # Cleanup
        cleanup_session(video_id)
        if user_id in processing_queue:
            del processing_queue[user_id]

async def process_single_conversion(callback_query, video_id, resolution, format_type, quality):
    """Process single video conversion"""
    session = video_sessions[video_id]
    input_file = session['path']
    
    output_file = f"outputs/{video_id}_{resolution}.{format_type}"
    
    start_time = time.time()
    
    try:
        await transcode_video(input_file, output_file, resolution, quality, format_type)
        
        processing_time = time.time() - start_time
        output_size = os.path.getsize(output_file)
        
        caption = f"""
🎬 **Conversion Complete!**

📐 Resolution: {resolution}
📁 Format: {format_type.upper()}
⚡ Quality: {quality}
⏱️ Processing time: {processing_time:.1f}s
📦 Output size: {format_file_size(output_size)}
💾 Compression: {((session['original_size'] - output_size) / session['original_size'] * 100):.1f}%
        """
        
        await callback_query.message.reply_video(
            video=output_file,
            caption=caption
        )
        
        os.remove(output_file)
        
    except Exception as e:
        raise Exception(f"Single conversion failed: {str(e)}")

async def process_batch_conversion(callback_query, video_id, batch_type):
    """Process batch video conversion"""
    session = video_sessions[video_id]
    input_file = session['path']
    
    batch_configs = {
        'all': [('240p', 'mp4'), ('360p', 'mp4'), ('480p', 'mp4'), ('720p', 'mp4'), ('1080p', 'mp4')],
        'mobile': [('240p', 'mp4'), ('360p', 'mp4')],
        'hd': [('720p', 'mp4'), ('1080p', 'mp4')]
    }
    
    configs = batch_configs.get(batch_type, [])
    total_files = len(configs)
    
    await callback_query.message.edit_text(f"⚙️ Processing {total_files} files...")
    
    for i, (resolution, format_type) in enumerate(configs, 1):
        try:
            output_file = f"outputs/{video_id}_{resolution}.{format_type}"
            
            await callback_query.message.edit_text(f"⚙️ Processing {i}/{total_files}: {resolution} {format_type.upper()}")
            
            await transcode_video(input_file, output_file, resolution, 'fast', format_type)
            
            output_size = os.path.getsize(output_file)
            
            caption = f"🎬 {resolution} {format_type.upper()} - {format_file_size(output_size)}"
            
            await callback_query.message.reply_video(
                video=output_file,
                caption=caption
            )
            
            os.remove(output_file)
            
        except Exception as e:
            await callback_query.message.reply(f"❌ Failed to process {resolution}: {str(e)}")
    
    await callback_query.message.edit_text("✅ Batch conversion complete!")

async def handle_admin_callback(client, callback_query):
    """Handle admin panel callbacks"""
    action = callback_query.data.replace("admin_", "")
    
    if action == "clear_cache":
        # Clear old sessions and files
        current_time = time.time()
        cleared = 0
        
        for video_id in list(video_sessions.keys()):
            session = video_sessions[video_id]
            if current_time - session['timestamp'] > 3600:  # 1 hour old
                cleanup_session(video_id)
                cleared += 1
        
        await callback_query.message.edit_text(f"🗑️ Cleared {cleared} old sessions")
    
    elif action == "detailed_stats":
        stats_text = "📊 **Detailed Statistics:**\n\n"
        
        total_users = len(user_stats)
        total_videos = sum(stats.get('videos_processed', 0) for stats in user_stats.values())
        
        stats_text += f"👥 Total Users: {total_users}\n"
        stats_text += f"🎬 Total Videos: {total_videos}\n"
        stats_text += f"📁 Active Sessions: {len(video_sessions)}\n"
        stats_text += f"⚙️ Processing Queue: {len(processing_queue)}\n"
        
        await callback_query.message.edit_text(stats_text)
    
    elif action == "restart":
        await callback_query.message.edit_text("🔄 Restarting bot...")
        # In a real deployment, you might want to implement graceful restart
        os._exit(0)

# Cleanup old sessions periodically
async def cleanup_old_sessions():
    """Cleanup old sessions every hour"""
    while True:
        try:
            current_time = time.time()
            for video_id in list(video_sessions.keys()):
                session = video_sessions[video_id]
                if current_time - session['timestamp'] > 3600:  # 1 hour
                    cleanup_session(video_id)
            
            await asyncio.sleep(3600)  # Run every hour
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            await asyncio.sleep(300)  # Retry in 5 minutes

if __name__ == "__main__":
    logger.info("Starting Advanced Video Encoder Bot...")
    
    # Start cleanup task
    asyncio.create_task(cleanup_old_sessions())
    
    # Run the bot
    app.run()