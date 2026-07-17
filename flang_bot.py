import logging
import os
import time
import asyncio

from dotenv import load_dotenv
load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from db import (
    init_db,
    get_or_create_user,
    get_user,
    set_active,
    set_interval,
    get_due_active_users,
    update_last_sent,
    get_random_word,
    get_current_word,
    set_current_word,
    record_sent_message,
    pop_old_messages,
)
from llm_groq import generate_sentence

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

SCHEDULER_TICK_SECONDS = 60  # тик планировщика, сек
WORD_REFRESH_SECONDS = 30 * 60  # раз в сколько меняем слово дня
KEEP_LAST_MESSAGES = 3  # сколько сообщений держим в чате максимум

INTERVAL_LABELS = {
    30: "30 минут",
    60: "1 час",
    120: "2 часа",
    1440: "24 часа",
}


def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("▶️ Старт", callback_data="start"),
            InlineKeyboardButton("⏸ Пауза", callback_data="pause"),
        ],
        [InlineKeyboardButton("⏱ Интервал", callback_data="interval_menu")],
    ])


def interval_keyboard():
    buttons = [
        [InlineKeyboardButton(label, callback_data=f"int_{minutes}")]
        for minutes, label in INTERVAL_LABELS.items()
    ]
    buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(buttons)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    get_or_create_user(update.effective_user.id)
    await update.message.reply_text(
        "🇩🇪 Бот для изучения немецких слов.\n\n"
        "Нажми ▶️ Старт, чтобы начать получать слова, и выбери интервал рассылки.",
        reply_markup=main_keyboard(),
    )


async def pause_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = get_or_create_user(update.effective_user.id)
    set_active(user_id, False)
    await update.message.reply_text(
        "⏸ Рассылка приостановлена.",
        reply_markup=main_keyboard(),
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    telegram_id = query.from_user.id
    user_id = get_or_create_user(telegram_id)
    data = query.data

    if data == "start":
        set_active(user_id, True)
        await query.edit_message_text(
            "✅ Рассылка включена. Присылаю первое слово...",
            reply_markup=main_keyboard(),
        )
        try:
            await send_word_to_user(context, user_id, telegram_id)
        except Exception:
            logger.exception("не удалось отправить первое слово user_id=%s", user_id)
        return

    if data == "pause":
        set_active(user_id, False)
        await query.edit_message_text(
            "⏸ Рассылка приостановлена.",
            reply_markup=main_keyboard(),
        )
        return

    if data == "back_to_menu":
        await query.edit_message_text(
            "🇩🇪 Бот для изучения немецких слов.",
            reply_markup=main_keyboard(),
        )
        return

    if data == "interval_menu":
        await query.edit_message_text(
            "⏱ Выбери, как часто присылать слово:",
            reply_markup=interval_keyboard(),
        )
        return

    if data.startswith("int_"):
        minutes = int(data.split("_")[1])
        set_interval(user_id, minutes)
        await query.edit_message_text(
            f"⏱ Интервал установлен: {INTERVAL_LABELS.get(minutes, minutes)}",
            reply_markup=main_keyboard(),
        )
        return


def ensure_current_word():
    # обновляем слово не чаще раза в WORD_REFRESH_SECONDS, чтобы экономить запросы к llm
    current = get_current_word()
    now = int(time.time())

    if current and now - current["generated_at"] < WORD_REFRESH_SECONDS:
        return current

    word = get_random_word()
    if not word:
        logger.warning("в таблице words нет слов")
        return None

    try:
        result = generate_sentence(word["word"], word["translation"], word.get("plural"))
    except Exception:
        logger.exception("не удалось сгенерировать предложение через groq")
        if current:
            return current  # лучше старое слово, чем ничего
        return None

    set_current_word(
        word_id=word["id"],
        word=word["word"],
        plural=word.get("plural"),
        translation=word["translation"],
        sentence_de=result["de"],
        sentence_ru=result["ru"],
    )
    return get_current_word()


def format_word_message(current_word: dict) -> str:
    plural_line = f"\n👥 Pl.: <b>{current_word['plural']}</b>" if current_word.get("plural") else ""
    return (
        "🇩🇪 <b>Слово дня</b>\n\n"
        f"<b>{current_word['word']}</b>{plural_line}\n"
        f"🇷🇺 {current_word['translation']}\n\n"
        f"💬 {current_word['sentence_de']}\n"
        f"🇷🇺 {current_word['sentence_ru']}"
    )


async def send_word_to_user(context: ContextTypes.DEFAULT_TYPE, user_id: int, telegram_id: int):
    current_word = ensure_current_word()
    if not current_word:
        return

    text = format_word_message(current_word)
    message = await context.bot.send_message(chat_id=telegram_id, text=text, parse_mode="HTML")
    update_last_sent(user_id)
    record_sent_message(user_id, message.message_id)
    await prune_old_messages(context, user_id, telegram_id)


def safe_keep_for_interval(interval_minutes: int) -> int:
    # раз в сутки телеграм не даст удалить старое сообщение (оно старше 48 часов) —
    # держим только последнее. для всех остальных интервалов держим KEEP_LAST_MESSAGES
    if interval_minutes >= 1440:
        return 1
    return KEEP_LAST_MESSAGES


async def prune_old_messages(context: ContextTypes.DEFAULT_TYPE, user_id: int, telegram_id: int):
    user = get_user(user_id)
    interval_minutes = user["interval_minutes"] if user else 60
    keep = safe_keep_for_interval(interval_minutes)

    old_message_ids = pop_old_messages(user_id, keep=keep)
    for message_id in old_message_ids:
        try:
            await context.bot.delete_message(chat_id=telegram_id, message_id=message_id)
        except Exception:
            logger.warning("не удалось удалить сообщение %s у user_id=%s", message_id, user_id)


async def scheduler(context: ContextTypes.DEFAULT_TYPE):
    due_users = get_due_active_users()
    if not due_users:
        return
    for user in due_users:
        try:
            await send_word_to_user(context, user["id"], user["telegram_id"])
        except Exception:
            logger.exception("не удалось отправить сообщение user_id=%s", user["id"])


async def post_init(application):
    # регистрируем команды, чтобы они появились в меню telegram
    await application.bot.set_my_commands([
        BotCommand("start", "Открыть меню / включить рассылку"),
        BotCommand("pause", "Поставить рассылку на паузу"),
    ])


def start_bot():
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не задан (переменная окружения)")

    # event loop сам не создается в главном потоке
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    init_db()

    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pause", pause_command))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.job_queue.run_repeating(scheduler, interval=SCHEDULER_TICK_SECONDS, first=10)

    logger.info("Bot läuft...")
    app.run_polling()


if __name__ == "__main__":
    start_bot()