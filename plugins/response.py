from pyrogram import Client, filters , ContinuePropagation ,enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton ,  ReplyKeyboardMarkup , ReplyKeyboardRemove
from .middlewares import authAdmin, check_user
from functions import get_admin_panel,get_manage_channels, get_user_tab,get_size,temp,save_file
from database.connection import Admin, Users
from pyrogram.errors import BadRequest, ChatAdminRequired , UsernameInvalid
import asyncio
from functions import temp , index_files_to_db, get_search_results
lock = asyncio.Lock()
from info import CANCEL_BUTTON,LOG_CHANNEL
import math


responses = {}


def create_response(message,target,payload={}):
    responses[message.from_user.id] = {"target":target,"payload":payload}
    
async def delete_response(message):
    if responses.get(message.from_user.id):
        await message.reply("<b>Welcome back!!!!</b>",reply_markup=ReplyKeyboardRemove(True))
        del responses[message.from_user.id]
        
    

    
    
@Client.on_message(filters.private)
async def get_add_channel(client, message):
    if not responses.get(message.from_user.id) or responses.get(message.from_user.id).get('target') != 'admin_channel_id': raise ContinuePropagation
    await delete_response(message)
    ans = message.text
    try:
        await client.get_chat_member(ans, message.from_user.id)
        Admin.update_one({"channels": 1}, {"$push": {"usernames": ans}}, upsert=True)
        await message.reply(f"<b>Channel Added To Bot: </b><code>{ans}</code>")
    except ChatAdminRequired:
        await message.reply("<b>Please promote bot as a admin in channel</b>")
    except UsernameInvalid:
        await message.reply("<b>Please send only channel chat id</b>")
    except Exception as err:
        await message.reply(f"An error occurred: {err}") 
    text, keyboard = await get_manage_channels(message, client)
    await message.reply(text, reply_markup=keyboard)


@Client.on_message(filters.private)
async def get_user_id(client, message):
    if not responses.get(message.from_user.id) or responses.get(message.from_user.id).get('target') != 'admin_user_id': raise ContinuePropagation
    ans = message.text
    if not ans.isdigit():
        return await message.reply("<b>Please give a valid user id</b>")
    userData = Users.find_one({"user_id": int(ans)})
    if not userData:
        await message.reply("<b>⛔️ User not found in our database</b>")
    await delete_response(message)
    text, keyboard = await get_user_tab(ans, userData)
    await message.reply(text, reply_markup=keyboard)




    

#Broacast
broad_data = {
    "users_done": 0, "broadcasting": False,
}

brake_after = 10 # help: Limit on the number of messages sent per second
messages_send_after_brake = 0
# help: We pause for 1 second after sending a certain number of messages. Telegram allows 30 messages per second, 
# help: so if we're sending more than that, we slow down to avoid being blocked by Telegram.

@Client.on_callback_query(filters.regex(r'^stop_broadcasting')|filters.private)
async def stop_broadcast(client,query):
    global messages_send_after_brake
    global broad_data
    await query.answer('Stopping broadcast...')
    await query.message.edit_text("<b>Brodcast stopped</b>")
    broad_data = {
    "users_done": 0, "broadcasting": False,
    }
    messages_send_after_brake = 0
    

@Client.on_message(filters.private)
async def broadcast_text(client, message):
    global messages_send_after_brake
    global broad_data
    if not responses.get(message.from_user.id) or responses.get(message.from_user.id).get('target') != 'admin_broadcast': raise ContinuePropagation
    ans = message.text
    await delete_response(message)
    if broad_data.get("broadcasting"):
        return await message.reply("<b>⚠️ Please wait until the previous broadcast gets completed</b>")
    usersData = Users.find({},{"_id":0,"user_id":1})
    hmsg = await message.reply(f"<b>⏳ Sending broadcast to users.....</b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⛔️ Stop','stop_broadcasting')]]))
    broad_data['broadcasting'] = True
    for i in usersData:
        userID = i.get('user_id')
        if not broad_data.get('broadcasting'): break
        if messages_send_after_brake is brake_after:
            await client.edit_message_text(
                message.from_user.id,
                hmsg.id,
                f"<b>⏳ Sleeping for 1 second\n\n✅ Broadcasted To: {broad_data.users_done} Users\n\n🗨 Users Left: {len(usersData) - broad_data['users_done']}</b>")
            await asyncio.sleep(1)
            messages_send_after_brake = 0
        messages_send_after_brake += 1
        try:
            if message.forward_from:
                await message.forward(userID)
            else:
                await message.copy(userID)
        except Exception as err:
            print(err)
        broad_data['users_done'] += 1
    await client.edit_message_text(message.from_user.id,hmsg.id,f"<b>✅ Broadcast completed \n\nBroadcasted To: {broad_data.get('users_done')} Users</b>")
    broad_data = {
    "users_done": 0, "broadcasting": False,
    }
    messages_send_after_brake = 0







#Indexing 
@Client.on_message(filters.forwarded & filters.private)
async def index_channel_link(client, message):
    if not responses.get(message.from_user.id) or responses.get(message.from_user.id).get('target') != 'admin_index_channel': raise ContinuePropagation
    ans = message.text
    if message.forward_from_chat.type == enums.ChatType.CHANNEL:
        last_msg_id = message.forward_from_message_id
        chat_id = message.forward_from_chat.id
    try:
        k = await client.get_messages(chat_id, last_msg_id)
    except:
        return await message.reply('Make Sure That Iam An Admin In The Channel, if channel is private')
    if k.empty:
        return await message.reply('This may be group and iam not a admin of the group.')
    if lock.locked():
            await delete_response(message)
            return await message.reply('Wait until previous process complete.')
    msg = message
    hmsg = await msg.reply('Processing...⏳')
    await client.edit_message_text(
            chat_id=message.from_user.id,
            message_id=hmsg.id,
            text="Starting Indexing",
            reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton('Cancel', callback_data='index_cancel')]]
            )
        )
        
    await index_files_to_db(last_msg_id, chat_id, hmsg, client)
    await delete_response(message)
    
    
    
BUTTONS = {}
#Related to providing providing movie
@Client.on_message(filters.private)
async def search_movie(_,msg):
    global BUTTONS
    if msg.text.startswith("/"): return
    query = msg.text
    files, offset, total_results = await get_search_results(query=query,max_results=10)
    if not files:
        return await msg.reply('<b>Sorry, we did not found this movie in our database</b>')
    btn = [
            [
                InlineKeyboardButton(
                    text=f"[{get_size(file.file_size)}] {file.file_name}", url=f"https://t.me/{temp.U_NAME}?start=file_{file.file_id}",
                ),
            ]
            for file in files
        ]
    if offset != "":
        key = f"{msg.chat.id}-{msg.id}"
        BUTTONS[key] = query
        req = msg.from_user.id if msg.from_user else 0
        btn.append(
            [InlineKeyboardButton(text=f"🗓 1/{math.ceil(int(total_results) / 10)}", callback_data="pages"),
             InlineKeyboardButton(text="NEXT ⏩", callback_data=f"next_{req}_{key}_{offset}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton(text="🗓 1/1", callback_data="pages")]
        )
    cap = f"Here is what i found for your query <u><i>{query}</u></i>"
    await msg.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))
    
    
@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    try:
        offset = int(offset)
    except:
        offset = 0
    search = BUTTONS.get(key)
    if not search:
        await query.answer("You are using one of my old messages, please send the request again.", show_alert=True)
        return

    files, n_offset, total = await get_search_results(search, offset=offset, filter=True)
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0

    if not files:
        return
    btn = [
            [
                InlineKeyboardButton(
                    text=f"[{get_size(file.file_size)}] {file.file_name}", url=f"https://t.me/{temp.U_NAME}?start=files_{file.file_id}"
                ),
            ]
            for file in files
        ]

    if 0 < offset <= 10:
        off_set = 0
    elif offset == 0:
        off_set = None
    else:
        off_set = offset - 10
    if n_offset == 0:
        btn.append(
            [InlineKeyboardButton("⏪ BACK", callback_data=f"next_{req}_{key}_{off_set}"),
             InlineKeyboardButton(f"📃 Pages {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}",
                                  callback_data="pages")]
        )
    elif off_set is None:
        btn.append(
            [InlineKeyboardButton(f"🗓 {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
             InlineKeyboardButton("NEXT ⏩", callback_data=f"next_{req}_{key}_{n_offset}")])
    else:
        btn.append(
            [
                InlineKeyboardButton("⏪ BACK", callback_data=f"next_{req}_{key}_{off_set}"),
                InlineKeyboardButton(f"🗓 {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
                InlineKeyboardButton("NEXT ⏩", callback_data=f"next_{req}_{key}_{n_offset}")
            ],
        )
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except:
        pass
    await query.answer()



#Indexing on new channel Post
@Client.on_message(filters.channel & filters.media)
async def onChannelPost(_,msg):
    if msg.media not in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.AUDIO, enums.MessageMediaType.DOCUMENT]: return ContinuePropagation()
    media = getattr(msg, msg.media.value, None)
    if not media: return ContinuePropagation()
    chatID = msg.chat.id
    indexedData = Admin.find_one({"indexed_channels":1})
    indexedChannels = indexedData['channels'] or []
    if not chatID in indexedChannels: return ContinuePropagation()
    media.file_type = msg.media.value
    media.caption = msg.caption
    aynav, vnay = await save_file(media,chatID)
    if aynav:
        try:
            text = f"<b>New media post indexed from {msg.chat.title}\n\nFile name:</b> <code>{media.file_name}</code>\n\n<b>File Size</b> <code>{get_size(media.file_size)}</code>"
            await _.send_message(chat_id=LOG_CHANNEL,text=text)
        except Exception as err:
            print(err)
    pass