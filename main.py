import os
import sys
import asyncio
import logging
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import (
ReplyKeyboardMarkup,
KeyboardButton,
InlineKeyboardMarkup,
InlineKeyboardButton
)
from pyrogram.enums import ChatMemberStatus

================= LOGGER =================

logging.basicConfig(
level=logging.INFO,
format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
handlers=[logging.StreamHandler(sys.stdout)]
)

logging.getLogger("pyrogram").setLevel(logging.WARNING)
ref_logger = logging.getLogger("REFERRAL")
ref_logger.setLevel(logging.INFO)

=========================================

================= CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN") or "8231560346:AAEYH6--lmZyOc3vyb2ju-tPkhDJf05rrvU"
API_ID = int(os.getenv("API_ID") or 36030323)
API_HASH = os.getenv("API_HASH") or "1d8fc7e8552f7141d5071f184af921e7"
MONGO_URL = os.getenv("MONGO_URL") or "mongodb+srv://sanjublogscom_db_user:Mahakal456@cluster0.cwi48dt.mongodb.net/?appName=Cluster0"

FORCE_CHANNEL_1 = "@payalgamingviralvideo123"
FORCE_CHANNEL_2 = "@payalgamingviralvideo123"

SUPPORT_ID = "@YourSupportUsername"
UPDATE_CHANNEL = "@YourUpdateChannel"

ADMIN_IDS = [6335046711]

=========================================

app = Client(
"referral_bot",
api_id=API_ID,
api_hash=API_HASH,
bot_token=BOT_TOKEN
)

mongo = MongoClient(MONGO_URL)
db = mongo["referralbot"]
users = db["users"]

================= MENU =================

def main_menu():
return ReplyKeyboardMarkup(
[
[KeyboardButton("🔗 My referrals"), KeyboardButton("📢 Updates")],
[KeyboardButton("📜 Rules"), KeyboardButton("🆘 Support")],
[KeyboardButton("📊 Leaderboard")]
],
resize_keyboard=True
)

================= FORCE JOIN =================

async def is_joined(user_id):
try:
ok = (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
m1 = await app.get_chat_member(FORCE_CHANNEL_1, user_id)
m2 = await app.get_chat_member(FORCE_CHANNEL_2, user_id)
return m1.status in ok and m2.status in ok
except:
return False

def force_buttons():
return InlineKeyboardMarkup(
[
[InlineKeyboardButton("✅ Join Channel 1", url=f"https://t.me/{FORCE_CHANNEL_1[1:]}")],
[InlineKeyboardButton("✅ Join Channel 2", url=f"https://t.me/{FORCE_CHANNEL_2[1:]}")],
[InlineKeyboardButton("🔄 Joined", callback_data="joined")]
]
)

================= START =================

async def start_handler(client, message):
uid = message.from_user.id
args = message.command if hasattr(message, "command") else []

user = users.find_one({"user_id": uid})  
if user and user.get("banned", 0) == 1:  
    await message.reply("🚫 You are banned from this bot.")  
    return  

ref_id = 0  
if len(args) > 1:  
    try:  
        ref_id = int(args[1])  
        if ref_id == uid:  
            ref_id = 0  
    except:  
        ref_id = 0  

if not user:  
    users.insert_one({  
        "user_id": uid,  
        "name": message.from_user.first_name or "User",  
        "referred_by": ref_id,  
        "referrals": 0,  
        "joined_confirmed": 0,  
        "banned": 0  
    })  

if not await is_joined(uid):  
    await message.reply(  
        "⚠️ Join both channels first",  
        reply_markup=force_buttons()  
    )  
    return  

await message.reply_photo(  
    photo="start.png",  
    caption="🔥 Referral Tournament Live 🔥",  
    reply_markup=main_menu()  
)

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
await start_handler(client, message)

================= JOINED =================

@app.on_callback_query(filters.regex("^joined$"))
async def joined(client, query):
uid = query.from_user.id
user = users.find_one({"user_id": uid})

if not user or user.get("joined_confirmed", 0) == 1:  
    return  

users.update_one({"user_id": uid}, {"$set": {"joined_confirmed": 1}})  

if user.get("referred_by"):  
    users.update_one(  
        {"user_id": user["referred_by"]},  
        {"$inc": {"referrals": 1}}  
    )  
    ref_logger.info(f"REF | {user['referred_by']} <- {uid}")  

await query.message.delete()  
await start_handler(client, query.message)

================= MENU =================

@app.on_message(filters.text & filters.private & ~filters.regex("^/"))
async def menu(client, message):
uid = message.from_user.id
user = users.find_one({"user_id": uid})

if user.get("banned", 0) == 1:  
    return  

if message.text == "📊 Leaderboard":  
    rows = users.find(  
        {"banned": {"$ne": 1}}  
    ).sort("referrals", -1).limit(30)  

    msg = "🏆 LEADERBOARD\n\n"  
    for i, u in enumerate(rows, 1):  
        msg += f"{i}. {u['name']} — {u['referrals']}\n"  

    await message.reply(msg)  

elif message.text == "🔗 My referrals":  
    me = await client.get_me()  
    await message.reply(  
        f"https://t.me/{me.username}?start={uid}"  
    )

================= ADMIN COMMANDS =================

@app.on_message(filters.command("resetlb") & filters.private)
async def reset_lb(_, message):
if message.from_user.id in ADMIN_IDS:
users.update_many({}, {"$set": {"referrals": 0}})
ref_logger.warning("ADMIN RESET LEADERBOARD")
await message.reply("✅ Leaderboard reset")

@app.on_message(filters.command("ban") & filters.private)
async def ban_user(_, message):
if message.from_user.id in ADMIN_IDS:
_, uid = message.text.split()
users.update_one({"user_id": int(uid)}, {"$set": {"banned": 1}})
await message.reply(f"🚫 User {uid} banned")

@app.on_message(filters.command("addref") & filters.private)
async def add_ref(_, message):
if message.from_user.id in ADMIN_IDS:
_, uid, c = message.text.split()
users.update_one({"user_id": int(uid)}, {"$inc": {"referrals": int(c)}})
await message.reply("✅ Added")

@app.on_message(filters.command("minusref") & filters.private)
async def minus_ref(_, message):
if message.from_user.id in ADMIN_IDS:
_, uid, c = message.text.split()
users.update_one({"user_id": int(uid)}, {"$inc": {"referrals": -int(c)}})
await message.reply("✅ Removed")

@app.on_message(filters.command("setref") & filters.private)
async def set_ref(_, message):
if message.from_user.id in ADMIN_IDS:
_, uid, c = message.text.split()
users.update_one({"user_id": int(uid)}, {"$set": {"referrals": int(c)}})
await message.reply("✅ Set")

================= RUN =================

print("🤖 Bot Started Successfully")
app.run()
