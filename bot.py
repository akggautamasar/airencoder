from pyrogram import Client, filters
import os
import subprocess
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Fetch credentials from environment variables
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("transcoder_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Create downloads directory if not exists
os.makedirs("downloads", exist_ok=True)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("👋 Send me a video file (max 2GB). I’ll transcode it into 360p, 480p, and 720p with watermark!")

@app.on_message(filters.video)
async def handle_video(client, message):
    msg = await message.reply("⬇️ Downloading video...")
    video_path = f"downloads/{message.video.file_id}.mp4"
    await message.download(file_name=video_path)

    await msg.edit("✅ Download complete. Choose the resolution to convert:")
    buttons = [
        [InlineKeyboardButton("360p", callback_data=f"360|{video_path}")],
        [InlineKeyboardButton("480p", callback_data=f"480|{video_path}")],
        [InlineKeyboardButton("720p", callback_data=f"720|{video_path}")],
        [InlineKeyboardButton("All (360+480+720)", callback_data=f"all|{video_path}")]
    ]
    await message.reply("🎯 Select output resolution:", reply_markup=InlineKeyboardMarkup(buttons))

def transcode(input_file, resolution, output_file):
    scale_map = {
        "360": "scale=-2:360",
        "480": "scale=-2:480",
        "720": "scale=-2:720"
    }
    watermark_text = "@YourBrand"
    cmd = [
        "ffmpeg", "-i", input_file,
        "-vf", f"{scale_map[resolution]},drawtext=text='{watermark_text}':fontcolor=white:fontsize=24:x=10:y=10",
        "-c:v", "libx264", "-preset", "fast", "-crf", "28",
        "-c:a", "aac", "-b:a", "128k", output_file, "-y"
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

@app.on_callback_query()
async def handle_callback(client, callback_query):
    data = callback_query.data
    resolution, input_file = data.split("|")

    await callback_query.message.edit_text("⚙️ Processing... Please wait.")

    output_files = []

    if resolution == "all":
        for res in ["360", "480", "720"]:
            out_file = f"{input_file}_{res}.mp4"
            transcode(input_file, res, out_file)
            output_files.append((res, out_file))
    else:
        out_file = f"{input_file}_{resolution}.mp4"
        transcode(input_file, resolution, out_file)
        output_files.append((resolution, out_file))

    for res, file_path in output_files:
        await callback_query.message.reply_video(
            video=file_path,
            caption=f"🎬 Converted to {res}p with watermark."
        )
        os.remove(file_path)

    os.remove(input_file)

    await callback_query.message.edit_text("✅ Done!")

app.run()
