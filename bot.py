from pyrogram import Client, filters
from pyrogram.types import Message
import os
import time
import subprocess

# Initialize your Pyrogram client
app = Client("my_bot")

# Function to calculate file size in a human-readable format
def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return f"{num:.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Yi{suffix}"

# Progress callback function for download
async def progress_for_pyrogram(current, total, message, start_time):
    # Calculate progress percentage
    progress_percent = (current / total) * 100
    elapsed_time = time.time() - start_time

    # Update message with progress status
    await message.edit(f"Downloading... {progress_percent:.2f}%\nElapsed Time: {elapsed_time:.2f} seconds")

# Command handler to trigger media download
@app.on_message(filters.command(["download"]))
async def download_media(bot, message: Message):
    try:
        # Initial message indicating download attempt
        ms = await message.reply("Trying to download...")

        # Download media file with progress callback
        file_path = "downloads/"
        await bot.download_media(
            message=message,
            file_name=file_path,
            progress=progress_for_pyrogram,
            progress_args=(ms, time.time())
        )

        # If download successful, update message
        await ms.edit("Download complete!")

    except Exception as e:
        # If an error occurs during download, update message with error details
        await ms.edit(f"Error downloading: {e}")

# Command handler to trigger stream removal
@app.on_message(filters.command(["removestream"]))
async def remove_stream(bot, message: Message):
    try:
        # Initial message indicating processing start
        ms = await message.reply("Processing video...")

        # Get media information
        file_info = message.video
        file_id = file_info.file_id
        file_size = file_info.file_size

        # Check file size (limit to 2 GB)
        max_file_size = 2 * 1024 * 1024 * 1024  # 2 GB in bytes
        if file_size > max_file_size:
            await ms.edit("Error: The video file is too large. Please send a smaller file.")
            return

        # Download video file (streaming approach)
        download_url = f'https://api.telegram.org/file/bot{app.export_session_string().split(":")[2]}/{file_info.file_path}'
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
        subprocess.run(ffmpeg_cmd, you execute even
