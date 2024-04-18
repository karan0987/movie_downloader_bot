import pymongo
from info import MONGO_URL , BOT_TOKEN


try:
    myclient = pymongo.MongoClient(MONGO_URL)
    mydb = myclient[BOT_TOKEN.split(":")[0]]
    Users = mydb['Users']
    TelegramFileCollection = "telegram_files"
    TelegramFiles = mydb[TelegramFileCollection]
    Admin = mydb['admin']
except Exception as err:
    print(f"Error while connecting MongDB: {err}")
    
