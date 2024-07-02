import telebot
import os
import subprocess
import time
from config import BOT_TOKEN

# Initialize the Telegram Bot
bot = telebot.TeleBot(BOT_TOKEN)

# Function to calculate file size in a human-readable format
def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return f"{num:.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Yi{suffix}"

# Function to calculate and return current time in a readable format
def current_time():
    return time.strftime('%H:%M:%S', time.gmtime())

# Handler for '/start' command
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "Welcome! Send me a video file and I will remove audio and subtitles.")

# Handler for video messages
@bot.message_handler(content_types=['video'])
def handle_video(message):
    try:
        # Check file size (limit to 2 GB)
        max_file_size = 2 * 1024 * 1024 * 1024  # 2 GB in bytes
        if message.video.file_size > max_file_size:
            bot.send_message(message.chat.id, "Error: The video file is too large. Please send a smaller file.")
            return

        # Inform user that download has started
        bot.send_message(message.chat.id, "Downloading video. Please wait...")

        # Define paths
        file_id = message.video.file_id
        video_filename = f"{file_id}.mp4"
        output_filename = f"processed_{file_id}.mp4"

        # Download video file (streaming approach)
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # Inform user that processing has started
        bot.send_message(message.chat.id, "Download complete. Processing video...")

        # Save video file locally
        with open(video_filename, 'wb') as f:
            f.write(downloaded_file)

        # Process video to remove audio and subtitles using ffmpeg
        start_time = time.time()
        ffmpeg_cmd = [
            'ffmpeg', '-i', video_filename,
            '-c:v', 'copy',       # Copy video stream
            '-an', '-sn',         # Remove audio and subtitles
            output_filename
        ]
        subprocess.run(ffmpeg_cmd, check=True)

        # Calculate processing time
        processing_time = time.time() - start_time

        # Inform user that upload has started
        bot.send_message(message.chat.id, "Processing complete. Uploading processed video...")

        # Send processed video back to user (streaming approach)
        start_time = time.time()
        with open(output_filename, 'rb') as f:
            bot.send_video(message.chat.id, f)

        # Calculate upload time
        upload_time = time.time() - start_time

        # Clean up temporary files
        os.remove(video_filename)
        os.remove(output_filename)

        # Format and send speed status messages
        download_speed = sizeof_fmt(os.path.getsize(video_filename) / processing_time) if processing_time > 0 else "N/A"
        upload_speed = sizeof_fmt(os.path.getsize(output_filename) / upload_time) if upload_time > 0 else "N/A"

        bot.send_message(message.chat.id, f"Download speed: {download_speed}/s\nUpload speed: {upload_speed}/s")

        # Inform user that upload is complete
        bot.send_message(message.chat.id, "Upload complete. Here is your processed video.")

    except Exception as e:
        bot.send_message(message.chat.id, f"Error processing video: {str(e)}")

# Handle all other messages
@bot.message_handler(func=lambda message: True)
def handle_all(message):
    bot.send_message(message.chat.id, "Send me a video file to process.")

# Polling to keep the bot running
bot.polling()
