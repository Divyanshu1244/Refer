import os
import asyncio
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from pyrogram.enums import ChatMemberStatus

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN") or "8231560346:AAEYH6--lmZyOc3vyb2ju-tPkhDJf05rrvU"
API_ID = int(os.getenv("API_ID") or 36030323)
API_HASH = os.getenv("API_HASH") or "1d8fc7e8552f7141d5071f184af921e7"

MONGO_URL = os.getenv("MONGO_URL") or "mongodb+srv://sanjublogscom_db_user:Mahakal456@cluster0.cwi48dt.mongodb.net/?appName=Cluster0"

FORCE_CHANNEL_1 = "@payalgamingviralvideo123"
FORCE_CHANNEL_2 = "@payalgamingviralvideo123"

SUPPORT_ID = "@YourSupportUsername"
UPDATE_CHANNEL = "@YourUpdateChannel"

ADMIN_IDS = [6335046711]
# =========================================

app = Client(
    "referral_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

mongo = MongoClient(MONGO_URL)
db = mongo["referralbot"]
users = db["users"]

# ================= MAIN MENU =================
def main_menu():
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("🔗 My referrals"),
                KeyboardButton("📢 Updates")
            ],
            [
                KeyboardButton("📜 Rules"),
                KeyboardButton("🆘 Support")
            ],
            [
                KeyboardButton("📊 Leaderboard")
            ]
        ],
        resize_keyboard=True
    )

# ================= FORCE JOIN CHECK =================
async def is_joined(user_id):
    try:
        m1 = await app.get_chat_member(FORCE_CHANNEL_1, user_id)
        m2 = await app.get_chat_member(FORCE_CHANNEL_2, user_id)
        ok = (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        )
        return (m1.status in ok) and (m2.status in ok)
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

# ================= START =================
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    uid = message.from_user.id
    args = message.command

    # ⏳ NORMAL LOADING (5 sec)
    loading = await message.reply("⏳ Loading...")
    await asyncio.sleep(5)
    try:
        await loading.delete()
    except:
        pass

    user = users.find_one({"user_id": uid})

    ref_id = 0
    if len(args) > 1:
        try:
            ref_id = int(args[1])
            if ref_id == uid:
                ref_id = 0
        except:
            ref_id = 0

    name = message.from_user.first_name or "User"

    if not user:
        users.insert_one({
            "user_id": uid,
            "name": name,
            "referred_by": ref_id,
            "referrals": 0,
            "joined_confirmed": 0
        })

    # 🔒 FORCE SUB
    if not await is_joined(uid):
        await message.reply(
            "⚠️ Pehle dono channels join karo.\nJoin ke baad **Joined** button dabao.",
            reply_markup=force_buttons()
        )
        return

    users.update_one(
        {"user_id": uid},
        {"$set": {"joined_confirmed": 1, "name": name}}
    )

    await message.reply(
        "🔥 *Referral Tournament Live!* 🔥\n\n"
        "👥 Refer friends & win rewards\n"
        "👇 Options niche diye gaye hain",
        reply_markup=main_menu()
    )

# ================= JOINED CALLBACK (AUTO /START) =================
@app.on_callback_query(filters.regex("^joined$"))
async def joined(client, query):
    uid = query.from_user.id

    if not await is_joined(uid):
        await query.answer("❌ Abhi dono channels join nahi hue", show_alert=True)
        return

    try:
        await query.message.delete()
    except:
        pass

    # AUTO /start
    fake_message = query.message
    fake_message.from_user = query.from_user
    fake_message.command = ["start"]

    await start(client, fake_message)

# ================= MENU =================
@app.on_message(filters.text & filters.private & ~filters.regex("^/"))
async def menu(_, message):
    uid = message.from_user.id
    text = message.text

    if not await is_joined(uid):
        await message.reply(
            "⚠️ Pehle dono channels join karo.\nJoin ke baad Joined button dabao.",
            reply_markup=force_buttons()
        )
        return

    if text == "🔗 My referrals":
        me = await app.get_me()
        link = f"https://t.me/{me.username}?start={uid}"
        user = users.find_one({"user_id": uid})
        count = user.get("referrals", 0) if user else 0
        await message.reply(
            f"🔗 Your Referral Link:\n{link}\n\n👥 Referrals: {count}"
        )

    elif text == "📊 Leaderboard":
        rows = users.find().sort("referrals", -1).limit(30)
        msg = "🏆 TOP LEADERBOARD\n\n"
        for i, u in enumerate(rows, start=1):
            msg += f"{i}. {u.get('name','User')} — {u.get('referrals',0)}\n"
        await message.reply(msg)

    elif text == "📜 Rules":
        await message.reply(
            "📜 RULES\n\n"
            "• Fake accounts not allowed\n"
            "• Force join mandatory\n"
            "• One user = one account\n"
            "• Final decision by system"
        )

    elif text == "📢 Updates":
        await message.reply(f"📢 Updates: {UPDATE_CHANNEL}")

    elif text == "🆘 Support":
        await message.reply(f"🆘 Support: {SUPPORT_ID}")

# ================= ADMIN =================
@app.on_message(filters.command("total") & filters.private)
async def total(_, message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.reply(f"👥 Total Users: {users.count_documents({})}")

@app.on_message(filters.command("broadcast") & filters.private)
async def broadcast(_, message):
    if message.from_user.id not in ADMIN_IDS:
        return

    if not message.reply_to_message:
        await message.reply("❌ Kisi message ko reply karke /broadcast likho")
        return

    sent, failed = 0, 0
    for u in users.find({}, {"user_id": 1}):
        try:
            await message.reply_to_message.copy(u["user_id"])
            sent += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1

    await message.reply(
        f"✅ Broadcast Done\n\n📤 Sent: {sent}\n❌ Failed: {failed}"
    )

print("🤖 Sanju i love you")
app.run()
