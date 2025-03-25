import re
import subprocess
import asyncio
import nest_asyncio
import logging
import os
import glob
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

nest_asyncio.apply()

# --- BOT CONFIGURATION ---
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Replace with your bot token
DEFAULT_DOWNLOAD_DIR = "/media/disk2/Movies"
DOCUMENTARIES_DIR = "/media/disk2/Documentaries"
SERIES_BASE_DIR = "/media/disk2/Series"
ANIME_BASE_DIR = "/media/disk2/Anime"
DOCUSERIES_BASE_DIR = "/media/disk2/DocuSeries"
ADMIN_CHAT_ID = -1001234567890  # Replace with your admin/group chat ID

# Base command for tdl (default template uses .FileName)
DOWNLOAD_CMD = r'tdl dl -u {url} -d {dir} -t 16 -l 9 --reconnect-timeout 0 --template "{{{{ .FileName }}}}"'

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.FileHandler("bot.log", encoding="utf-8")]
)
logger = logging.getLogger()

# --- ConversationHandler States ---
SERIES_NAME, SERIES_SEASON = range(2)
ANIME_NAME, ANIME_SEASON = range(2)
DOC_NAME, DOC_SEASON = range(2)

# --- Common Functions ---
def get_message_link(message):
    """Generates the Telegram message link."""
    chat = message.chat
    if chat.username:
        return f"https://t.me/{chat.username}/{message.message_id}"
    else:
        chat_id_str = str(chat.id)
        base = chat_id_str[4:] if chat_id_str.startswith("-100") else chat_id_str.lstrip("-")
        return f"https://t.me/c/{base}/{message.message_id}"

async def run_download(cmd, retries=3, delay=5):
    """
    Executes the tdl command and shows a single-line progress indicator.
    Captures output from the command and updates in the same console line.
    """
    for attempt in range(1, retries + 1):
        logger.info(f"Attempt {attempt} of {retries} to run: {cmd}")
        print(f"Attempt {attempt} of {retries} to run: {cmd}")
        proc = await asyncio.to_thread(
            subprocess.Popen,
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        last_line = ""
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            last_line = line.strip()
            # Overwrite the same console line with progress info
            print("\r" + last_line, end="", flush=True)
        proc.wait()
        print("")  # Newline after finishing
        if proc.returncode == 0:
            logger.info("Download completed.")
            return True
        else:
            logger.error(f"Error on attempt {attempt}: exit code {proc.returncode}")
            print(f"Error on attempt {attempt}: exit code {proc.returncode}")
            if attempt < retries:
                logger.info(f"Retrying in {delay} seconds...")
                print(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
            else:
                return False

def extract_rar(directory):
    """
    Searches for .rar files in the directory. If multiple parts exist,
    it assumes the extraction should start with the file containing "part1".
    If not found, it takes the first .rar file.
    Then it extracts using unrar and deletes all .rar files in the directory.
    """
    rar_files = glob.glob(os.path.join(directory, "*.rar"))
    file_to_extract = None

    if rar_files:
        for rar in rar_files:
            if "part1" in os.path.basename(rar).lower():
                file_to_extract = rar
                break
        if file_to_extract is None:
            file_to_extract = rar_files[0]

    if file_to_extract:
        try:
            cmd_extract = f'unrar x -o+ "{file_to_extract}" "{directory}"'
            logger.info(f"Extracting: {cmd_extract}")
            print(f"Extracting: {cmd_extract}")
            subprocess.run(cmd_extract, shell=True, check=True)
            for f in rar_files:
                os.remove(f)
            logger.info(f"Extracted and deleted rar files from: {file_to_extract}")
            print(f"Extracted and deleted rar files from: {file_to_extract}")
        except Exception as e:
            logger.error(f"Error extracting {file_to_extract}: {e}")
            print(f"Error extracting {file_to_extract}: {e}")

# --- /start Command ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "Welcome to CineBot!\n\n"
        "Available options:\n"
        "• Movies: /peliculas 🎬\n"
        "• Series: /serie 📺\n"
        "• Anime: /anime ✨\n"
        "• Docu-Series: /docuseries 📼\n\n"
        "Send a Telegram link and the file will be downloaded."
    )
    await update.message.reply_text(message)

# --- Message Handler for Downloads ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    chat_title = message.chat.title if message.chat.title else str(message.chat.id)
    identifier = f"[{chat_title}-{message.message_id}]"

    if message.text and re.search(r'https://t\.me', message.text):
        link = message.text.strip()
    elif any([message.document, message.video, message.audio, message.photo]):
        link = get_message_link(message)
    else:
        return

    logger.info(f"Received link or file from {identifier}: {link}")
    print(f"Received link or file from {identifier}: {link}")

    download_dir = context.chat_data.get("download_dir", DEFAULT_DOWNLOAD_DIR)
    extra_flags = context.chat_data.get("tdl_extra_flags", "")
    # Wrap directory in quotes to preserve spaces
    cmd = DOWNLOAD_CMD.format(url=link, dir=f'"{download_dir}"')
    if extra_flags:
        cmd += " " + extra_flags

    await context.bot.send_message(chat_id=message.chat.id, text="⏳ Downloading...")
    print(f"Downloading to: {download_dir}")
    print(f"Executing command: {cmd}")
    if await run_download(cmd):
        # Set success message based on download type
        if extra_flags == "--group":
            if "series_name" in context.user_data:
                name = context.user_data.pop("series_name")
                success_msg = f"📺 The series '{name}' has finished downloading."
            elif "anime_name" in context.user_data:
                name = context.user_data.pop("anime_name")
                success_msg = f"✨ The anime '{name}' has finished downloading."
            elif "doc_name" in context.user_data:
                name = context.user_data.pop("doc_name")
                success_msg = f"📼 The docu-series '{name}' has finished downloading."
            else:
                success_msg = "Download completed successfully."
        else:
            success_msg = f"Download completed successfully.\nLink: {link}"
        logger.info(success_msg)
        print(success_msg)
        await context.bot.send_message(chat_id=message.chat.id, text=success_msg)
        try:
            await context.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        except Exception as e:
            logger.error(f"Error deleting message: {e}")
            print(f"Error deleting message: {e}")
        if extra_flags == "--group":
            extract_rar(download_dir)
    else:
        error_msg = f"{identifier} Error during download. Please verify the link or try again."
        logger.error(error_msg)
        print(error_msg)
        await context.bot.send_message(chat_id=message.chat.id, text=error_msg)

# --- Handlers for Movies and Documentaries ---
async def set_movies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.chat_data["download_dir"] = DEFAULT_DOWNLOAD_DIR
    context.chat_data.pop("tdl_extra_flags", None)
    msg = "Download directory set to Movies 🎬"
    await update.message.reply_text(msg)
    logger.info(msg)
    print(msg)

async def set_documentaries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.chat_data["download_dir"] = DOCUMENTARIES_DIR
    context.chat_data.pop("tdl_extra_flags", None)
    msg = "Download directory set to Documentaries 🎬"
    await update.message.reply_text(msg)
    logger.info(msg)
    print(msg)

# --- ConversationHandlers for Series, Anime, and Docu-Series ---
# For Series
async def series_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter the series name:")
    return SERIES_NAME

async def series_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    series_name = update.message.text.strip()
    context.user_data["series_name"] = series_name
    await update.message.reply_text(f"Series: {series_name}.\nNow, enter the season number:")
    return SERIES_SEASON

async def series_season(update: Update, context: ContextTypes.DEFAULT_TYPE):
    season_input = update.message.text.strip()
    try:
        season_number = int(season_input)
    except ValueError:
        await update.message.reply_text("Please enter a valid season number:")
        return SERIES_SEASON
    series_name = context.user_data.get("series_name", "Unknown")
    season_formatted = f"Season {season_number:02d}"
    series_dir = os.path.join(SERIES_BASE_DIR, series_name, season_formatted)
    print("Series directory configured:", series_dir)
    os.makedirs(series_dir, exist_ok=True)
    context.chat_data["download_dir"] = series_dir
    context.chat_data["tdl_extra_flags"] = "--group"
    await update.message.reply_text(f"Download directory set for series: {series_dir}")
    return ConversationHandler.END

# For Anime
async def anime_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter the anime name:")
    return ANIME_NAME

async def anime_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    anime_name = update.message.text.strip()
    context.user_data["anime_name"] = anime_name
    await update.message.reply_text(f"Anime: {anime_name}.\nNow, enter the season number:")
    return ANIME_SEASON

async def anime_season(update: Update, context: ContextTypes.DEFAULT_TYPE):
    season_input = update.message.text.strip()
    try:
        season_number = int(season_input)
    except ValueError:
        await update.message.reply_text("Please enter a valid season number:")
        return ANIME_SEASON
    anime_name = context.user_data.get("anime_name", "Unknown")
    season_formatted = f"Season {season_number:02d}"
    anime_dir = os.path.join(ANIME_BASE_DIR, anime_name, season_formatted)
    print("Anime directory configured:", anime_dir)
    os.makedirs(anime_dir, exist_ok=True)
    context.chat_data["download_dir"] = anime_dir
    context.chat_data["tdl_extra_flags"] = "--group"
    await update.message.reply_text(f"Download directory set for anime: {anime_dir}")
    return ConversationHandler.END

# For Docu-Series
async def docuseries_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter the docu-series name:")
    return DOC_NAME

async def doc_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc_name = update.message.text.strip()
    context.user_data["doc_name"] = doc_name
    await update.message.reply_text(f"Docu-Series: {doc_name}.\nNow, enter the season number:")
    return DOC_SEASON

async def doc_season(update: Update, context: ContextTypes.DEFAULT_TYPE):
    season_input = update.message.text.strip()
    try:
        season_number = int(season_input)
    except ValueError:
        await update.message.reply_text("Please enter a valid season number:")
        return DOC_SEASON
    doc_name = context.user_data.get("doc_name", "Unknown")
    season_formatted = f"Season {season_number:02d}"
    doc_dir = os.path.join(DOCUSERIES_BASE_DIR, doc_name, season_formatted)
    print("Docu-Series directory configured:", doc_dir)
    os.makedirs(doc_dir, exist_ok=True)
    context.chat_data["download_dir"] = doc_dir
    context.chat_data["tdl_extra_flags"] = "--group"
    await update.message.reply_text(f"Download directory set for docu-series: {doc_dir}")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

async def notify_admin(bot, text):
    try:
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)
    except Exception as e:
        logger.error(f"Error notifying admin: {e}")
        print(f"Error notifying admin: {e}")

async def main():
    print("Waiting for work...")
    app = Application.builder().token(BOT_TOKEN).build()

    from telegram.ext import ConversationHandler

    series_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("serie", series_start)],
        states={
            SERIES_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, series_name)],
            SERIES_SEASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, series_season)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    anime_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("anime", anime_start)],
        states={
            ANIME_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, anime_name)],
            ANIME_SEASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, anime_season)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    doc_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("docuseries", docuseries_start)],
        states={
            DOC_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, doc_name)],
            DOC_SEASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, doc_season)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # Register handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("peliculas", set_movies))
    app.add_handler(CommandHandler("documentales", set_documentaries))
    app.add_handler(series_conv_handler)
    app.add_handler(anime_conv_handler)
    app.add_handler(doc_conv_handler)
    # Remove /opciones handler and ignore CallbackQueryHandler if not needed
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    
    try:
        await app.run_polling()
    except Exception as e:
        err_msg = f"Bot closed or failed: {e}"
        print(err_msg)
        await notify_admin(app.bot, err_msg)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
