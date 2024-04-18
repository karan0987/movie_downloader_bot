from pyrogram import Client, filters 
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .middlewares import check_join, check_user
from functions import get_file_details,get_size
import base64
import asyncio
from database.connection import TelegramFiles, Users

@Client.on_message(filters.command('start') | filters.regex(r'\bJoined\b') & filters.private)
async def start(client,message):
    if not await check_user(client,message): return
    if not await check_join(client,message): return
    
    if message.text == '/start' or message.text == 'Joined':
        photo = "./pictures/stall.png"
        caption = "<b>Hello!!!\n\n🍿 Welcome to the world's coolest search engine!</b>"
        keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔥 Hot Movies", url="https://t.me/ArNetworksLtd")
        ],
        [
            InlineKeyboardButton("ℹ️ Bot Info",callback_data='bot_info')
        ],
        [
            InlineKeyboardButton("🌟 Rate Me",url='https://t.me/ArNetworksLtd')
        ]
        ])
        return await message.reply_photo(photo,caption=caption,reply_markup=keyboard)
        
    kk, file_id = message.command[1].split("_", 1) if "_" in message.command[1] else (False, False)
    files_ = await get_file_details(file_id)  
    data = message.command[1]
    
    if not files_:
        pre, file_id = ((base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("ascii")).split("_", 1)
        try:
            msg = await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=file_id,
                protect_content=True if pre == 'filep' else False,
                )
            filetype = msg.media
            file = getattr(msg, filetype)
            title = file.file_name
            size=get_size(file.file_size)
            f_caption = f"<code>{title}</code>\n\n<b>File Size:</b> <code>{size}</code>"
            await msg.edit_caption(f_caption)
        except:
            pass
    else:
        files = files_[0]
        title = files.file_name
        size=get_size(files.file_size)
        f_caption=files.caption
        if f_caption is None:
           f_caption = f"{files.file_name}"
        msg = await client.send_cached_media(
           chat_id=message.from_user.id,
           file_id=file_id,
           caption=f_caption,
        )
    msg_1 = await message.reply("<b>‼️ 𝗜𝗠𝗣𝗢𝗥𝗧𝗔𝗡𝗧 ‼️\n\n⚠️ 𝙁𝙞𝙡𝙚 𝙒𝙞𝙡𝙡 𝘽𝙚 𝘿𝙚𝙡𝙚𝙩𝙚𝙙 𝙄𝙣 𝟱 𝙈𝙞𝙣𝙪𝙩𝙚𝙨.\n\n�𝗳 𝘆𝗼𝘂 𝘄𝗮𝗻𝘁 𝘁𝗼 𝗱𝗼𝘄𝗻𝗹𝗼𝗮𝗱 𝘁𝗵𝗶𝘀 𝗳𝗶𝗹𝗲, 𝗞𝗶𝗻𝗱𝗹𝘆 𝗙𝗼𝗿𝘄𝗮𝗿𝗱 𝘁𝗵𝗶𝘀 𝗳𝗶𝗹𝗲 𝘁𝗼 𝗮𝗻𝘆 𝗰𝗵𝗮𝘁 (𝘀𝗮𝘃𝗲𝗱) 𝗮𝗻𝗱 𝘀𝘁𝗮𝗿𝘁 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱...</b>")
    await asyncio.sleep(5*60)
    try:
        await client.delete_messages(message.from_user.id,[msg_1.id,msg.id])
    except Exception as err:
        print(err)
    
        
    


@Client.on_callback_query(filters.regex(r'^bot_info'))
async def bot_info(_,query):
    photo = '../pictures/stall.png'
    total_files = TelegramFiles.count_documents({})
    total_users = Users.count_documents({})
    caption = f"""<b>Total Files:</b> <code>{total_files}</code>\n<b>Total Users:</b> <code>{total_users}</code>"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🆘 Tutorial",url="https://t.me/ArNetworksLtd"),
            InlineKeyboardButton("👥 Group Chat",url="https://t.me/ArNetworksLtd")
        ],
        [
            InlineKeyboardButton("DISCLAIMER‼️",'disclaimer')
        ]
    ])
    await query.message.edit(text=caption,reply_markup=keyboard)
    pass


@Client.on_callback_query(filters.regex(r'^disclaimer'))
async def disclaimer(_,query):
    text = """<b>DISCLAIMER‼️</b>\nIt is forbidden to download, stream, reproduce, or by any means, share, or consume, content without explicit permission from the content creator or legal copyright holder. Contact the respective channels for removal if you believe this bot violates your intellectual property.The Bot does not own any of these contents , it only index the files from telegram."""
    await query.message.edit(text=text,reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Back','bot_info')]]))