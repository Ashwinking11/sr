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

# Function to send status message with download or upload progress
def send_status_message(chat_id, message):
    return bot.send_message(chat_id, message)

# Function to process video
def process_video(message):
    try:
        chat_id = message.chat.id
        file_id = message.video.file_id
        max_file_size = 2 * 1024 * 1024 * 1024  # 2 GB in bytes

        # Check file size (limit to 2 GB)
        if message.video.file_size > max_file_size:
            send_status_message(chat_id, "Error: The video file is too large. Please send a smaller file.")
            return

        # Inform user that processing has started
        status_message = send_status_message(chat_id, "Processing video...")

        # Download video file (streaming approach)
        file_info = bot.get_file(file_id)
        download_url = f'https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}'
        video_filename = f"{file_id}.mp4"

        # Process video to remove audio and subtitles using ffmpeg (chunked processing)
        start_time = time.time()
        output_filename = f"processed_{file_id}.mp4"
        ffmpeg_cmd = [
            'ffmpeg', '-i', download_url,
            '-c:v', 'copy',       # Copy video stream
            '-an', '-sn',         # Remove audio and subtitles
            output_filename
        ]
        subprocess.run(ffmpeg_cmd, check=True)

        # Calculate processing time and speed
        processing_time = time.time() - start_time
        processed_size = os.path.getsize(output_filename)
        processing_speed = processed_size / processing_time if processing_time > 0 else 0

        # Send processed video back to user
        with open(output_filename, 'rb') as f:
            bot.send_video(chat_id, f, caption="Processed video")

        # Clean up temporary files
        os.remove(output_filename)

        # Send final status message with processing details
        status_message_text = f"Processing complete\nTime taken: {processing_time:.2f} seconds\nProcessed size: {sizeof_fmt(processed_size)}\nProcessing speed: {sizeof_fmt(processing_speed)}/s"
        bot.edit_message_text(chat_id=chat_id, message_id=status_message.message_id, text=status_message_text)

    except Exception as e:
        send_status_message(chat_id, f"Error processing video: {str(e)}")

# Handler for '/start' command
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "Welcome! Send me a video file and I will remove audio and subtitles.")

# Handler for video messages
@bot.message_handler(content_types=['video'])
def handle_video(message):
    process_video(message)

# Handle all other messages
@bot.message_handler(func=lambda message: True)
def handle_all(message):
    bot.send_message(message.chat.id, "Send me a video file to process.")

# Polling to keep the bot running
bot.polling()
