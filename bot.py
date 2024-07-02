import telebot
import os
import subprocess
from config import BOT_TOKEN

# Initialize the Telegram Bot
bot = telebot.TeleBot(BOT_TOKEN)

# Handler for '/start' command
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "Welcome! Send me a video file and I will remove audio and subtitles.")

# Handler for video messages
@bot.message_handler(content_types=['video'])
def handle_video(message):
    try:
        # Check file size (limit to 20MB)
        max_file_size = 20000 * 1024 * 1024  # 20 MB in bytes
        if message.video.file_size > max_file_size:
            bot.send_message(message.chat.id, "Error: The video file is too large. Please send a smaller file.")
            return
        
        # Download video file
        file_id = message.video.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Save video file locally
        video_filename = f"{file_id}.mp4"
        with open(video_filename, 'wb') as f:
            f.write(downloaded_file)
        
        # Process video to remove audio and subtitles using ffmpeg
        output_filename = f"processed_{file_id}.mp4"
        ffmpeg_cmd = [
            'ffmpeg', '-i', video_filename,
            '-c:v', 'copy',       # Copy video stream
            '-an', '-sn',         # Remove audio and subtitles
            output_filename
        ]
        subprocess.run(ffmpeg_cmd, check=True)

        # Send processed video back to user
        with open(output_filename, 'rb') as f:
            bot.send_video(message.chat.id, f)
        
        # Clean up temporary files
        os.remove(video_filename)
        os.remove(output_filename)
    
    except Exception as e:
        bot.send_message(message.chat.id, f"Error processing video: {str(e)}")

# Handle all other messages
@bot.message_handler(func=lambda message: True)
def handle_all(message):
    bot.send_message(message.chat.id, "Send me a video file to process.")

# Polling to keep the bot running
bot.polling()
