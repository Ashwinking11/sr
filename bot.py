from pyrogram import Client, filters
from pyrogram.types import Message
import os
import time
import subprocess
from config import BOT_TOKEN, API_ID, API_HASH

# Initialize your Pyrogram client
app = Client(
    "my_bot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH
)

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
        # Check if message contains media
        if not (message.video or message.document or message.audio):
            await message.reply("This message doesn't contain any downloadable media.")
            return

        # Initial message indicating download attempt
        ms = await message.reply("Trying to download...")

        # Determine the type of media and set the file_path accordingly
        if message.video:
            file_path = "downloads/video.mp4"
            media = message.video
        elif message.document:
            file_path = "downloads/document"
            media = message.document
        elif message.audio:
            file_path = "downloads/audio.mp3"
            media = message.audio

        # Download media file with progress callback
        await bot.download_media(
            message=media,
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
        # Check if message contains video
        if not message.video:
            await message.reply("This message doesn't contain a video.")
            return

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

        # Download video file
        path = await bot.download_media(message=file_info, file_name=file_id + ".mp4", progress=progress_for_pyrogram, progress_args=(ms, time.time()))

        # Process video to remove audio and subtitles using ffmpeg
        start_time = time.time()
        output_filename = f"processed_{file_id}.mp4"
        ffmpeg_cmd = [
            'ffmpeg', '-i', path,
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
            await bot.send_video(chat_id=message.chat.id, video=f, caption="Processed video")

        # Clean up temporary files
        os.remove(output_filename)

        # Send final status message with processing details
        status_message_text = f"Processing complete\nTime taken: {processing_time:.2f} seconds\nProcessed size: {sizeof_fmt(processed_size)}\nProcessing speed: {sizeof_fmt(processing_speed)}/s"
        await ms.edit(status_message_text)

    except Exception as e:
        await ms.edit(f"Error processing video: {str(e)}")

# Start the bot
app.run()
