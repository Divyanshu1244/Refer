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
BOT_TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN"
API_ID = int(os.getenv("API_ID") or 123456)
API_HASH = os.getenv("API_HASH") or "YOUR_API_HASH"

MONGO_URL = os.getenv("MONGO_URL") or "YOUR_MONGO_URL"

FORCE_CHANNEL_1 = "@payalgamingviralvideo123"
FORCE_CHANNEL_2 = "@payalgamingviralvideo123"

SUPPORT_ID = "@support"
UPDATE_CHANNEL = "@updates"

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

# ================= MENU =================
def main_menu():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🔗 My referrals"), KeyboardButton("📢 Updates")],
            [KeyboardButton("📊 Leaderboard"), KeyboardButton("📍 My Position")],
            [KeyboardButton("📜 Rules"), KeyboardButton("🆘 Support")]
        ],
        resize_keyboard=True
    )

# ================= FORCE JOIN =================
async def is_joined(uid):
    try:
        ok = (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        )
        m1 = await app.get_chat_member(FORCE_CHANNEL_1, uid)
        m2 = await app.get_chat_member(FORCE_CHANNEL_2, uid)
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

# ================= START =================
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    uid = message.from_user.id
    args = message.command

    ref = int(args[1]) if len(args) > 1 and args[1].isdigit() else 0
    if ref == uid:
        ref = 0

    user = users.find_one({"user_id": uid})

    if not user:
        users.insert_one({
            "user_id": uid,
            "referred_by": ref,
            "referrals": 0,
            "banned": 0
        })

        # ✅ CREDIT REFERRAL ONLY ONCE
        if ref != 0:
            users.update_one(
                {"user_id": ref},
                {"$inc": {"referrals": 1}}
            )

    if not await is_joined(uid):
        await message.reply(
            "⚠️ Pehle dono channels join karo.\nJoin ke baad Joined button dabao.",
            reply_markup=force_buttons()
        )
        return

    await message.reply(
        "🔥 Referral Tournament Live!\n\n"
        "👥 Refer friends & win rewards\n"
        "👇 Options niche diye gaye hain",
        reply_markup=main_menu()
    )

# ================= JOINED CALLBACK (SAFE) =================
@app.on_callback_query(filters.regex("^joined$"))
async def joined(client, query):
    if not await is_joined(query.from_user.id):
        await query.answer("❌ Join both channels first", show_alert=True)
        return

    await query.message.delete()
    await client.send_message(query.from_user.id, "/start")

# ================= MENU =================
@app.on_message(filters.text & filters.private)
async def menu(_, message):
    uid = message.from_user.id
    text = message.text

    user = users.find_one({"user_id": uid})
    if not user or user.get("banned"):
        return

    if text == "🔗 My referrals":
        me = await app.get_me()
        link = f"https://t.me/{me.username}?start={uid}"
        await message.reply(
            f"🔗 Your Referral Link:\n{link}\n\n"
            f"👥 Referrals: {user['referrals']}"
        )

    elif text == "📊 Leaderboard":
        rows = users.find(
            {"referrals": {"$gt": 0}, "banned": 0}
        ).sort("referrals", -1).limit(95)

        msg = "🏆 TOP LEADERBOARD\n\n"

        for i, u in enumerate(rows, start=1):
            if i == 1: prize = "30k"
            elif i == 2: prize = "23k"
            elif i == 3: prize = "15k"
            elif i in (4, 5): prize = "8k"
            elif 6 <= i <= 15: prize = "5k"
            elif 16 <= i <= 30: prize = "3k"
            else: prize = "—"

            msg += f"{i}. {u['user_id']} — {u['referrals']} | {prize}\n"

        await message.reply(msg)

    elif text == "📍 My Position":
        rows = list(
            users.find({"referrals": {"$gt": 0}, "banned": 0})
            .sort("referrals", -1)
        )

        rank = next((i+1 for i, u in enumerate(rows) if u["user_id"] == uid), None)
        if not rank:
            return await message.reply(
                "❌ Abhi tum leaderboard me nahi ho.\n"
                "👉 Pehle referral lao."
            )

        if rank == 1: prize = "30k"
        elif rank == 2: prize = "23k"
        elif rank == 3: prize = "15k"
        elif rank in (4, 5): prize = "8k"
        elif 6 <= rank <= 15: prize = "5k"
        elif 16 <= rank <= 30: prize = "3k"
        else: prize = "—"

        await message.reply(
            f"📍 Your Position\n\n"
            f"🏆 Rank: {rank}\n"
            f"👥 Referrals: {user['referrals']}\n"
            f"💰 Prize: {prize}"
        )

    elif text == "📜 Rules":
        await message.reply(
            "📜 RULES\n\n"
            "• Fake accounts not allowed\n"
            "• One user = one account\n"
            "• Force join mandatory"
        )

    elif text == "📢 Updates":
        await message.reply(UPDATE_CHANNEL)

    elif text == "🆘 Support":
        await message.reply(SUPPORT_ID)

# ================= ADMIN COMMANDS =================
def is_admin(m): 
    return m.from_user.id in ADMIN_IDS

@app.on_message(filters.command("lbreset") & filters.private)
async def lbreset(_, m):
    if not is_admin(m): return
    users.update_many({}, {"$set": {"referrals": 0}})
    await m.reply("✅ Leaderboard reset")

@app.on_message(filters.command("addref") & filters.private)
async def addref(_, m):
    if not is_admin(m): return
    uid, amt = map(int, m.command[1:])
    users.update_one({"user_id": uid}, {"$inc": {"referrals": amt}})
    await m.reply("✅ Referrals added")

@app.on_message(filters.command("minusref") & filters.private)
async def minusref(_, m):
    if not is_admin(m): return
    uid, amt = map(int, m.command[1:])
    users.update_one({"user_id": uid}, {"$inc": {"referrals": -amt}})
    await m.reply("✅ Referrals removed")

@app.on_message(filters.command("ban") & filters.private)
async def ban(_, m):
    if not is_admin(m): return
    users.update_one({"user_id": int(m.command[1])}, {"$set": {"banned": 1}})
    await m.reply("🚫 User banned")

@app.on_message(filters.command("unban") & filters.private)
async def unban(_, m):
    if not is_admin(m): return
    users.update_one({"user_id": int(m.command[1])}, {"$set": {"banned": 0}})
    await m.reply("✅ User unbanned")

@app.on_message(filters.command("total") & filters.private)
async def total(_, m):
    if not is_admin(m): return
    await m.reply(f"👥 Total users: {users.count_documents({})}")

@app.on_message(filters.command("broadcast") & filters.private)
async def broadcast(_, m):
    if not is_admin(m): return
    if not m.reply_to_message:
        return await m.reply("Reply to a message")

    for u in users.find({}, {"user_id": 1}):
        try:
            await m.reply_to_message.copy(u["user_id"])
            await asyncio.sleep(0.05)
        except:
            pass

    await m.reply("✅ Broadcast done")

print("🤖 BOT STARTED (FINAL BUILD)")
app.run()
