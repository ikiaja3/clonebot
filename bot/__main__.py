from telegram.ext import CommandHandler, run_async
from bot.gDrive import GoogleDriveHelper
from bot.fs_utils import get_readable_file_size
from bot import LOGGER, dispatcher, updater, bot, CLONE_DICT
from bot.config import BOT_TOKEN, OWNER_ID, GDRIVE_FOLDER_ID
from bot.decorators import is_authorised, is_owner
from telegram.error import TimedOut, BadRequest
from bot.clone_status import CloneStatus
from bot.msg_utils import deleteMessage, sendMessage
import time

REPO_LINK = "https://stream.iki.my.id"
# Soon to be used for direct updates from within the bot.

@run_async
def start(update, context):
    sendMessage("Halo! Kirimkan saya Tautan Google Drive yang Dapat Dibagikan untuk Mengkloning ke Drive!" \
        "\nKetik /help untuk memeriksa semua perintah yang tersedia.",
    context.bot, update, 'Markdown')
    # ;-;

@run_async
def helper(update, context):
    sendMessage("Berikut adalah perintah bot yang tersedia\n\n" \
        "*Usage:* `/clone <link> [DESTINATION_ID]`\n*Example:* \n1. `/clone https://drive.google.com/drive/u/1/folders/0AO-ISIXXXXXXXXXXXX`\n2. `/clone 0AO-ISIXXXXXXXXXXXX`" \
            "\n*DESTIONATION_ID* bersifat opsional. Ini bisa berupa tautan atau ID ke tempat Anda ingin menyimpan klon tertentu." \
            "\n\nKamu juga bisa*mengabaikan folder* dari proses klon dengan melakukan hal berikut:\n" \
                "`/clone <FOLDER_ID> [DESTINATION] [id1,id2,id3]`\n Dalam contoh ini: id1, id2 dan id3 akan diabaikan dari kloning\nDo not use <> or [] dalam pesan yang sebenarnya." \
                    "*Pastikan untuk tidak memberi spasi di antara koma (,).*\n" \
                        f"Kunjungi Web: [KLIK AKU]({REPO_LINK})", context.bot, update, 'Markdown')


@run_async
@is_authorised
def cloneNode(update,context):
    global CLONE_DICT
    args = update.message.text.split(" ")
    if len(args) > 1:
        link = args[1]
        try:
            ignoreList = args[-1].split(',')
        except IndexError:
            ignoreList = []

        DESTINATION_ID = GDRIVE_FOLDER_ID
        try:
            DESTINATION_ID = args[2]
            print(DESTINATION_ID)
        except IndexError:
            pass
            # Usage: /clone <FolderToClone> <Destination> <IDtoIgnoreFromClone>,<IDtoIgnoreFromClone>

        msg = sendMessage(f"<b>Cloning:</b> <code>{link}</code>", context.bot, update)
        gd = GoogleDriveHelper(GFolder_ID=DESTINATION_ID)
        status_class = CloneStatus(gd)
        folder_id = gd.getIdFromUrl(link)
        CLONE_DICT[folder_id] = status_class
        status_class.folderID = folder_id
        sendCloneStatus(update, context, status_class, msg, link)
        result = gd.clone(link, status_class, ignoreList=ignoreList)
        deleteMessage(context.bot, msg)
        status_class.set_status(True)
        sendMessage(result, context.bot, update)
    else:
        sendMessage("Harap Berikan Tautan Google Drive Publik untuk digandakan.", bot, update)


@run_async
def sendCloneStatus(update, context, status, msg, link):
    old_text = ''
    while not status.done():
        sleeper(3)
        try:
            text=f'🔗 *Cloning:* [{status.MainFolderName}]({status.MainFolderLink})\n━━━━━━━━━━━━━━\n🗃️ *Current File:* `{status.get_name()}`\n⬆️ *Transferred*: `{status.get_size()}`\n📁 *Destination:* [{status.DestinationFolderName}]({status.DestinationFolderLink})'
            if status.checkFileStatus():
                text += f"\n🕒 *Checking Existing Files:* `{str(status.checkFileStatus())}`"
            text += f"\n❌ /`cancel {status.folderID}`"
            if not text == old_text:
                msg.edit_text(text=text, parse_mode="Markdown", timeout=200)
                old_text = text
        except Exception as e:
            # LOGGER.error(e) # So people stop spamming me
            if str(e) == "Message to edit not found":
                break
            sleeper(2)
            continue
    return

def sleeper(value, enabled=True):
    time.sleep(int(value))
    return

@run_async
@is_owner
def sendLogs(update, context):
    with open('log.txt', 'rb') as f:
        bot.send_document(document=f, filename=f.name,
                        reply_to_message_id=update.message.message_id,
                        chat_id=update.message.chat_id)

@run_async
@is_authorised
def cancelClone(update, context):
    args = update.message.text.split(" ")
    if len(args) > 1:
        uid = args[1]
    else:
        sendMessage("Sebutkan ID klon yang ingin Anda batalkan.", context.bot, update)
        return
    
    cloneObj = CLONE_DICT[uid]
    cloneObj.set_status(True)
    cloneObj.cancelClone()
    sendMessage("Clone should get cancelled now.", context.bot, update)


def main():
    LOGGER.info("Bot Started!")
    clone_handler = CommandHandler('clone', cloneNode)
    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', helper)
    log_handler = CommandHandler('logs', sendLogs)
    cancel_hander = CommandHandler('cancel', cancelClone)
    dispatcher.add_handler(log_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(clone_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(cancel_hander)
    updater.start_polling()

main()
