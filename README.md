# Advanced Video Encoder Bot

A powerful Telegram bot for video transcoding with multiple format support, quality presets, and batch processing capabilities.

## Features

### 🎬 Video Processing
- **Multiple Resolutions**: 240p, 360p, 480p, 720p, 1080p
- **Various Formats**: MP4, MKV, AVI, WebM, MOV
- **Quality Presets**: Ultra Fast to Very Slow encoding
- **Custom Watermarks**: Add your brand/text overlay
- **Batch Processing**: Convert multiple resolutions at once

### 🚀 Advanced Features
- **Progress Tracking**: Real-time conversion progress
- **Video Analysis**: Detailed video information display
- **Smart Compression**: Optimal bitrate selection
- **Queue Management**: Handle multiple users efficiently
- **Admin Panel**: System monitoring and management
- **Usage Statistics**: Track user activity and processing

### 🛡️ Reliability
- **Error Handling**: Comprehensive error management
- **Session Management**: Automatic cleanup of old files
- **Resource Monitoring**: CPU, memory, and disk usage tracking
- **Health Checks**: Built-in health monitoring for deployment

## Deployment on Render

### Prerequisites
1. Create a Telegram bot via [@BotFather](https://t.me/BotFather)
2. Get your Telegram API credentials from [my.telegram.org](https://my.telegram.org)
3. Create a [Render](https://render.com) account

### Environment Variables

Set these environment variables in your Render dashboard:

#### Required Variables
- `API_ID` - Your Telegram API ID (integer)
- `API_HASH` - Your Telegram API Hash (string)
- `BOT_TOKEN` - Your bot token from BotFather

#### Optional Variables
- `ADMIN_IDS` - Comma-separated list of admin user IDs (e.g., "123456789,987654321")
- `MAX_FILE_SIZE` - Maximum file size in bytes (default: 2147483648 = 2GB)
- `WATERMARK_TEXT` - Text to overlay on videos (default: "@YourBrand")
- `MAX_CONCURRENT_PROCESSES` - Max simultaneous conversions (default: 3)
- `SESSION_TIMEOUT` - Session timeout in seconds (default: 3600)
- `DEFAULT_QUALITY` - Default encoding quality (default: "fast")
- `DEFAULT_RESOLUTION` - Default resolution (default: "720p")
- `DEFAULT_FORMAT` - Default output format (default: "mp4")

### Deployment Steps

1. **Fork this repository** or create a new one with these files

2. **Connect to Render**:
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

3. **Configure the service**:
   - **Name**: `video-encoder-bot`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
   - **Plan**: Free (or paid for better performance)

4. **Set Environment Variables**:
   - Add all required environment variables in the Render dashboard
   - Make sure to set `API_ID`, `API_HASH`, and `BOT_TOKEN`

5. **Deploy**:
   - Click "Create Web Service"
   - Wait for deployment to complete

### Getting Your Telegram Credentials

#### API_ID and API_HASH
1. Go to [my.telegram.org](https://my.telegram.org)
2. Log in with your phone number
3. Go to "API Development Tools"
4. Create a new application
5. Copy your `api_id` and `api_hash`

#### BOT_TOKEN
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot`
3. Follow the instructions to create your bot
4. Copy the bot token provided

#### ADMIN_IDS (Optional)
1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. Copy your user ID
3. Add it to the `ADMIN_IDS` environment variable

## Usage

### Basic Commands
- `/start` - Welcome message and bot introduction
- `/help` - Detailed help and instructions
- `/stats` - Your usage statistics
- `/formats` - List of supported formats and resolutions
- `/admin` - Admin panel (admins only)

### Video Processing
1. **Send a video file** to the bot (max 2GB)
2. **Choose conversion type**:
   - **Quick Convert**: Fast processing with good quality
   - **Advanced Options**: Custom resolution, format, and quality
   - **Batch Convert**: Multiple resolutions at once
3. **Wait for processing** - Progress will be shown
4. **Download** your converted video(s)

### Conversion Options

#### Resolutions
- **240p** - Low quality, small file size
- **360p** - Standard quality for mobile
- **480p** - Good quality for web
- **720p** - HD quality (recommended)
- **1080p** - Full HD quality

#### Quality Presets
- **Ultra Fast** - Fastest processing, larger files
- **Fast** - Good balance of speed and quality
- **Medium** - Better quality, moderate speed
- **Slow** - High quality, slower processing
- **Very Slow** - Best quality, slowest processing

#### Output Formats
- **MP4** - Most compatible, recommended
- **MKV** - High quality container
- **AVI** - Legacy compatibility
- **WebM** - Web optimized
- **MOV** - Apple/QuickTime compatible

## Technical Details

### System Requirements
- **CPU**: Multi-core recommended for faster processing
- **RAM**: 512MB minimum, 1GB+ recommended
- **Storage**: 10GB+ for temporary files
- **FFmpeg**: Required for video processing

### Performance Optimization
- Uses efficient FFmpeg presets
- Automatic cleanup of temporary files
- Queue management for multiple users
- Resource monitoring and limits

### Security Features
- User session isolation
- File size limits
- Processing timeouts
- Admin-only commands
- Automatic cleanup

## Troubleshooting

### Common Issues

#### Bot not responding
- Check if all environment variables are set correctly
- Verify bot token is valid
- Check Render logs for errors

#### Conversion failures
- Ensure input file is a valid video
- Check if file size is within limits
- Verify FFmpeg is working (should be automatic)

#### Out of memory errors
- Reduce `MAX_CONCURRENT_PROCESSES`
- Use faster quality presets
- Process smaller files

### Monitoring
- Use `/admin` command to check system status
- Monitor Render dashboard for resource usage
- Check logs for error messages

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For support and questions:
1. Check the troubleshooting section
2. Review Render logs
3. Create an issue on GitHub
4. Contact the bot admin (if you're a user)

---

**Note**: This bot is designed for educational and personal use. Ensure you comply with Telegram's Terms of Service and respect copyright laws when processing videos.