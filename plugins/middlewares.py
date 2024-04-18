from database.connection import Admin , Users
import asyncio
from info import ADMINS
from functions import check_channel_member,get_channel_details
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup , KeyboardButton


async def check_user(client,message):
    from_user = getattr(message,'from_user')
    user_id = getattr(from_user,'id',False)
    if not user_id: return False
    userData = Users.find_one({"user_id":user_id})
    if not userData:
        Users.insert_one({"user_id":user_id}) 
        userData = {}
        
    if user_id in ADMINS:
        return True
    
    botData = Admin.find_one({"admin":1}) or {}
    botStatus = "is_bot_down" in botData
    if botStatus:
        await message.reply('<b>Bot is currently under maintaince</b>')
        return False
    
    banStatus = 'is_ban' in userData
    if banStatus:
        await message.reply("<b>You are banned from using this bot</b>")
        return False
    return True


async def check_join(client,message):
    channels_data = Admin.find_one({"channels":1}) or {}
    channels = channels_data.get('usernames') or []
    results = await asyncio.gather(*[
        check_channel_member(client, channel, message.from_user.id)
        for channel in channels
    ])
    if "left" in results or "BANNED" in  results :
        channelsDetails = await asyncio.gather(*[
        get_channel_details(client,channel)
        for channel in channels
        ])
        channelsDetails=list(filter(lambda x: x != 'none', channelsDetails))
        text = f"<b>Join our channels before using this bot\n</b>"
        for i in channelsDetails: text += f"\n{i.get('invite_link')}"
        keyboard = ReplyKeyboardMarkup(
            [
                [KeyboardButton('Joined')]
            ]
            ,resize_keyboard=True)
        await message.reply(text,reply_markup=keyboard)
        return False
    return True



async def authAdmin(client,message):
    from_user = getattr(message,'from_user')
    user_id = getattr(from_user,'id',False)
    if not user_id: return False
    if user_id not in ADMINS: return False
    return True