from pyrogram import Client, filters 
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton , ReplyKeyboardMarkup, KeyboardButton
from .middlewares import authAdmin, check_user
from functions import get_admin_panel,get_manage_channels,get_user_tab,get_indexed_channels,temp
from database.connection import Admin, Users , TelegramFiles
from .response import create_response , delete_response
from pyrogram.errors import ChatAdminRequired 
from info import CANCEL_BUTTON

cancel_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton(CANCEL_BUTTON)]
],resize_keyboard=True)


@Client.on_message(filters.command(['admin','panel']) | filters.regex(rf'\b{CANCEL_BUTTON}\b'))
async def admin(_,msg):
    await delete_response(msg)
    if not await authAdmin(_,msg):return
    text,keyboard = await get_admin_panel(msg)
    await msg.reply(text,reply_markup=keyboard)
    
@Client.on_callback_query(filters.regex(r'^manage_channels'))
async def manage_channels(_,query):
    if not await authAdmin(_,query):return
    text , keyboard = await get_manage_channels(query,_)
    await query.message.edit_text(text,reply_markup=keyboard)
    pass
    
@Client.on_callback_query(filters.regex(r'^add_channel'))
async def add_channel(_,query):
    if not await authAdmin(_,query):return
    await query.message.delete()
    text = "<b>Send channel id make sure bot is admin in that channel</b>"
    await query.message.reply(text,reply_markup=cancel_keyboard)
    create_response(query,'admin_channel_id')
    pass
    
@Client.on_callback_query(filters.regex(r'^/check_channel'))
async def check_channel(_,query):
    if not await authAdmin(_,query):return
    channelID = query.data.split(maxsplit=1)[1]
    try:
        await _.get_chat_member(channelID,query.from_user.id)
        await query.answer(f"✅ There's no any problem with this channel")
    except ChatAdminRequired:
        await query.answer(f"Please promote bot as a admin in channel")
    except Exception as err:
        await query.message.reply(f"An error accured: {err}") 
    
@Client.on_callback_query(filters.regex(r'^/delete_channel'))
async def delete_channel(_,query):
    if not await authAdmin(_,query):return
    channelID = query.data.split(maxsplit=1)[1]
    Admin.update_one({"channels":1},{"$pull":{"usernames":channelID}})
    await query.answer('Channel Removed From Bot') 
    text , keyboard = await get_manage_channels(query,_)
    await query.message.edit_text(text,reply_markup=keyboard)
    pass
   
   

@Client.on_callback_query(filters.regex(r'^enable_bot'))
async def enable_bot(_,query):
    if not await authAdmin(_,query):return
    Admin.update_one({"admin":1},{"$unset":{"is_bot_down":True}},upsert=True)
    text,keyboard = await get_admin_panel(query)
    await query.message.edit_text(text,reply_markup=keyboard)
    pass


@Client.on_callback_query(filters.regex(r'^disable_bot'))
async def disable_bot(_,query):
    if not await authAdmin(_,query):return
    Admin.update_one({"admin":1},{"$set":{"is_bot_down":True}},upsert=True)
    text,keyboard = await get_admin_panel(query)
    await query.message.edit_text(text,reply_markup=keyboard)
    pass

@Client.on_callback_query(filters.regex(r'^/ban'))
async def ban_user(_,query):
    if not await authAdmin(_,query):return
    user_id = query.data.split(maxsplit=1)[1]
    Users.update_one({"user_id":int(user_id)},{"$set":{"is_ban":True}})
    text,keyboard = await get_user_tab(int(user_id))
    await query.message.edit_text(text,reply_markup=keyboard)
    pass 

@Client.on_callback_query(filters.regex(r'^/unban'))
async def unban_user(_,query):
    if not await authAdmin(_,query):return
    user_id = query.data.split(maxsplit=1)[1]
    Users.update_one({"user_id":int(user_id)},{"$unset":{"is_ban":True}})
    text,keyboard = await get_user_tab(int(user_id))
    await query.message.edit_text(text,reply_markup=keyboard)
    pass 


@Client.on_callback_query(filters.regex(r'^user_settings'))
async def user_settings(_,query):
    if not await authAdmin(_,query):return
    await query.message.delete()
    text = "<b>Send user telegram ID</b>"
    await query.message.reply(text,reply_markup=cancel_keyboard)
    create_response(query,'admin_user_id')
    pass



@Client.on_callback_query(filters.regex(r'^index_channel'))
async def index_channel(_,query):
    if not await authAdmin(_,query):return
    text , keyboard = await get_indexed_channels(_,query)
    await query.message.edit_text(text,reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r'^/del_index'))
async def delete_channel(_,query):
    if not await authAdmin(_,query):return
    channelID = query.data.split(maxsplit=1)[1]
    Admin.update_one({"indexed_channels":1},{"$pull":{"channels":int(channelID)}})
    TelegramFiles.delete_many({"chat_id":int(channelID)})
    await query.answer('Channel Indexed Files Removed From Bot') 
    text , keyboard = await get_indexed_channels(_,query)
    await query.message.edit_text(text=text,reply_markup=keyboard)
    pass
   

#Broadcast
@Client.on_callback_query(filters.regex(r'^broadcast'))
async def broadcast(client,query):
    if not await authAdmin(client,query):return
    await query.message.delete()
    text = "<b>Send or Forward message text to broadcast</b>"
    await query.message.reply(text,reply_markup=cancel_keyboard)
    create_response(query,'admin_broadcast')
    pass




#Indexing
@Client.on_callback_query(filters.regex(r'^/index_channel'))
async def index_a_channel(_,query):
    if not await authAdmin(_,query):return
    await query.message.delete()
    text = "<b>Forward Me the last post of channel , you want to index files</b>"
    await query.message.reply(text,reply_markup=cancel_keyboard)
    create_response(query,'admin_index_channel')
    pass


@Client.on_callback_query(filters.regex(r'^stop_indexing'))
async def stop_indexing(_,query):
    if not await authAdmin(_,query):return
    temp.CANCEL = True
    return await query.message.edit_text('<b>indexing stopped</b>')    