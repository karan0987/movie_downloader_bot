from database.connection import Admin , Users , TelegramFileCollection ,mydb
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
from pyrogram import enums,Client
from pyrogram.errors import UserNotParticipant
from pyrogram.file_id import FileId
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
import re
from struct import pack
import base64
from marshmallow.exceptions import ValidationError
lock = asyncio.Lock()

async def check_channel_member(client, channel, user_id):
    try:
        member = await client.get_chat_member(channel, user_id)
        return member.status.name
    except UserNotParticipant as e:
        return 'left'
    except:
        return 'error'


async def get_admin_panel(msg, admin_data=None):
    admin_data = admin_data or Admin.find_one({"admin": 1}) or {}
    bot_status = "Enabled" if not admin_data.get('is_bot_down') else "Disabled"
    button_text = "Enable" if admin_data.get('is_bot_down') else "Disable"
    hello_message = f"""Hello Master {msg.from_user.first_name}!!!"""
    text = f"""<b>{hello_message}
Bot: {bot_status}
</b>"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"{button_text} Bot", "enable_bot" if admin_data.get('is_bot_down') else "disable_bot")
        ],
        [
            InlineKeyboardButton("Manage Channels",'manage_channels')
        ],
        [
            InlineKeyboardButton('User Settings','user_settings')
        ],
        [
            InlineKeyboardButton('Broadcast','broadcast')
        ],
        [
            InlineKeyboardButton('Indexed Channels','index_channel')
        ]
    ])
    return text, keyboard



async def get_manage_channels(msg,client,channelsData=None,):
    channelsData = channelsData or Admin.find_one({"channels":1}) or {}
    channels = channelsData["usernames"] or []
    text = "<b>Manage your Channels\n\nuse 'Delete' button to remove channel</b>"
    keyboard = []
    channelsDetails = await asyncio.gather(*[
        get_channel_details(client,channel)
        for channel in channels
    ])
    channelsDetails=list(filter(lambda x: x != 'none', channelsDetails))
    for channel in channelsDetails:
        keyboard.append([
            InlineKeyboardButton(channel.get('title'),f"/check_channel {channel.get('channel_id')}"),
            InlineKeyboardButton("Delete",f"/delete_channel {channel.get('channel_id')}"),
            ])
    keyboard.append([InlineKeyboardButton('Add Channel','add_channel')])
    keyboard = InlineKeyboardMarkup(keyboard)
    return text , keyboard
                
async def get_user_tab(user_id:int,userData=None):
    userData = userData or Users.find_one({"user_id":user_id})
    if not userData: return False
    text = f"""<b>
    🤖 User account details found
    
    User ID: {user_id}
    </b>"""
    if userData.get('is_ban'): text+="<b>Status: Banned</b>" 
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Ban" if not userData.get('is_ban') else "Unban",f"/ban {user_id}" if not userData.get('is_ban') else f"/unban {user_id}")]
    ])
    return text , keyboard
                
async def get_channel_details(client,chat_id):
    try:
        chatData = await client.get_chat(chat_id=int(chat_id))
        return {
            "title":chatData.title,
            "invite_link":chatData.invite_link,
            "channel_id":chatData.id
        }
    except Exception as err:
        print(err)
        return 'none'
        
        
        
async def get_indexed_channels(client,message):
    indexedData  = Admin.find_one({"indexed_channels":1}) or {}
    indexedChannels = indexedData.get('channels') or []
    channelsDetails =  await asyncio.gather(*[
        get_channel_details(client,channel)
        for channel in indexedChannels
    ])
    text = "<b>Indexed Channels:</b>\n"
    for i in channelsDetails:
        text += f"\n{i['title']}: {i['invite_link']}"
    keyboard = []
    for i in channelsDetails:
        keyboard.append([InlineKeyboardButton(i['title'],'/non'),InlineKeyboardButton('Delete',f"/del_index {i['channel_id']}")])
    keyboard.append([InlineKeyboardButton('Index a channel','/index_channel')])
    keyboard = InlineKeyboardMarkup(keyboard)
    return text,keyboard 




# Function Related To Indexing

instance = Instance.from_db(mydb)
@instance.register
class Media(Document):
    chat_id = fields.IntegerField(required=True)
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)

    class Meta:
        indexes = ('$file_name', )
        collection_name = TelegramFileCollection

class temp(object):
    ME = None
    CANCEL = False
    CURRENT = 0


async def index_files_to_db(lst_msg_id, chat, msg, bot):
    total_files = 0
    duplicate = 0
    errors = 0
    deleted = 0
    no_media = 0
    unsupported = 0
    can = [[InlineKeyboardButton('Cancel', callback_data='stop_indexing')]]
    reply = InlineKeyboardMarkup(can)
    async with lock:
        try:
            current = temp.CURRENT
            temp.CANCEL = False
            Admin.update_one({"indexed_channels":1},{"$push":{"channels":chat}},upsert=True)
            async for message in bot.iter_messages(chat, lst_msg_id, temp.CURRENT):
                if temp.CANCEL:
                    await msg.edit_text(f"Successfully Cancelled!!\n\nSaved <code>{total_files}</code> files to dataBase!\nDuplicate Files Skipped: <code>{duplicate}</code>\nDeleted Messages Skipped: <code>{deleted}</code>\nNon-Media messages skipped: <code>{no_media + unsupported}</code>(Unsupported Media - `{unsupported}` )\nErrors Occurred: <code>{errors}</code>")
                    break
                current += 1
                if current % 20 == 0:
                    await msg.edit_text(
                        text=f"Total messages fetched: <code>{current}</code>\nTotal messages saved: <code>{total_files}</code>\nDuplicate Files Skipped: <code>{duplicate}</code>\nDeleted Messages Skipped: <code>{deleted}</code>\nNon-Media messages skipped: <code>{no_media + unsupported}</code>(Unsupported Media - `{unsupported}` )\nErrors Occurred: <code>{errors}</code>",
                        reply_markup=reply)
                if message.empty:
                    deleted += 1
                    continue
                elif not message.media:
                    no_media += 1
                    continue
                elif message.media not in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.AUDIO, enums.MessageMediaType.DOCUMENT]:
                    unsupported += 1
                    continue
                media = getattr(message, message.media.value, None)
                if not media:
                    unsupported += 1
                    continue
                media.file_type = message.media.value
                media.caption = message.caption
                aynav, vnay = await save_file(media,chat)
                if aynav:
                    total_files += 1
                elif vnay == 0:
                    duplicate += 1
                elif vnay == 2:
                    errors += 1
        except Exception as e:
            print(e)
            await msg.edit(f'Error: {e}',reply_markup=reply)
        else:
            await msg.edit(f'Succesfully saved <code>{total_files}</code> to dataBase!\nDuplicate Files Skipped: <code>{duplicate}</code>\nDeleted Messages Skipped: <code>{deleted}</code>\nNon-Media messages skipped: <code>{no_media + unsupported}</code>(Unsupported Media - `{unsupported}` )\nErrors Occurred: <code>{errors}</code>')





async def save_file(media,chat_id):
    """Save file in database"""

    # TODO: Find better way to get same file_id for same media to avoid duplicates
    file_id, file_ref = unpack_new_file_id(media.file_id)
    file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
    try:
        file = Media(
            chat_id=chat_id,
            file_id=file_id,
            file_ref=file_ref,
            file_name=file_name,
            file_size=media.file_size,
            file_type=media.file_type,
            mime_type=media.mime_type,
            caption=media.caption.html if media.caption else None,
        )
    except ValidationError as err:
        print('Error occurred while saving file in database',err)
        return False, 2
    else:
        try:
            file.commit()
        except DuplicateKeyError:      
            print(
                f'{getattr(media, "file_name", "NO_FILE")} is already saved in database'
            )

            return False, 0
        else:
            print(f'{getattr(media, "file_name", "NO_FILE")} is saved to database')
            return True, 1



async def get_search_results(query, file_type=None, max_results=10, offset=0, filter=False):
    """For given query return (results, next_offset)"""
    query = query.strip()
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_]')
    
    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except:
        return []

    if True:
        filter = {'$or': [{'file_name': regex}, {'caption': regex}]}
    else:
        filter = {'file_name': regex}

    if file_type:
        filter['file_type'] = file_type

    total_results = Media.count_documents(filter)
    next_offset = offset + max_results

    if next_offset > total_results:
        next_offset = ''

    cursor = Media.find(filter)
    # Sort by recent
    cursor.sort('$natural', -1)
    # Slice files according to offset and max results
    cursor.skip(offset).limit(max_results)
    # Get list of files
    files = cursor
    return files, next_offset, total_results





async def get_file_details(query):
    filter = {'file_id': query}
    cursor = Media.find(filter)
    filedetails = cursor
    return filedetails


def encode_file_id(s: bytes) -> str:
    r = b""
    n = 0

    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0

            r += bytes([i])

    return base64.urlsafe_b64encode(r).decode().rstrip("=")


def encode_file_ref(file_ref: bytes) -> str:
    return base64.urlsafe_b64encode(file_ref).decode().rstrip("=")


def unpack_new_file_id(new_file_id):
    """Return file_id, file_ref"""
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(
        pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash
        )
    )
    file_ref = encode_file_ref(decoded.file_reference)
    return file_id, file_ref



def get_size(size):
    """Get size in readable format"""

    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])