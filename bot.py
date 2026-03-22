import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from fpdf import FPDF
from datetime import datetime

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")

# Conversation states
HOTEL_NAME, ADDRESS, PHONE, DURATION, CHECK_IN, CHECK_OUT, GUEST_INFO, ROOM_TYPE, ROOM_VIEW, MEAL_PLAN, AMOUNT_PAID = range(11)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать в Hotels Voucher Bot! 🏨\n\n"
        "Я помогу вам создать ваучер для отеля.\n\n"
        "Используйте команду /generate_voucher, чтобы начать создание ваучера."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/generate_voucher - Создать PDF-ваучер\n"
        "/cancel - Отменить создание ваучера\n"
        "/help - Показать это сообщение"
    )

async def generate_voucher_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Header
    pdf.set_fill_color(36, 47, 65) # Dark blue
    pdf.rect(0, 0, 210, 30, 'F')
    pdf.set_text_color(255, 255, 255) # White
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, txt=data.get("hotel_name", "Hotel Name"), ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 10, txt=f"Confirmation Number: R{datetime.now().strftime('%Y%m%d%H%M%S')}", ln=True, align="C")
    pdf.ln(5)

    pdf.set_text_color(0, 0, 0) # Black
    pdf.set_font("Helvetica", "B", 12)

    # Sections helper
    def add_section(title, fields):
        pdf.set_fill_color(36, 47, 65)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 10, txt=title, ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)
        for label, value in fields:
            pdf.cell(40, 7, txt=f"{label}:", border=0)
            pdf.cell(0, 7, txt=str(value), ln=True)
        pdf.ln(5)

    add_section("PROPERTY INFORMATION", [
        ("Address", data.get("address", "N/A")),
        ("Phone", data.get("phone", "N/A"))
    ])

    add_section("STAY DETAILS", [
        ("Duration", data.get("duration", "N/A")),
        ("Check-in", data.get("check_in", "N/A")),
        ("Check-out", data.get("check_out", "N/A"))
    ])

    guest_list = data.get("guest_info", "N/A").split(",")
    guests = [(f"Guest {i+1}", g.strip()) for i, g in enumerate(guest_list)]
    add_section("GUEST INFORMATION", guests)

    add_section("ROOM & SERVICES", [
        ("Room Type", data.get("room_type", "N/A")),
        ("Room View", data.get("room_view", "N/A")),
        ("Meal Plan", data.get("meal_plan", "N/A"))
    ])

    add_section("PAYMENT INFORMATION", [
        ("Amount Paid", data.get("amount_paid", "N/A"))
    ])

    # Important Information
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, txt="Important Information", ln=True)
    pdf.set_font("Helvetica", "", 10)
    info_text = (
        "• Please present this voucher upon arrival at the hotel.\n"
        "• A valid photo ID and credit card may be required at check-in.\n"
        "• Check-in time is as indicated above. Early check-in is subject to availability.\n"
        "• Late check-out requests should be made directly with the hotel."
    )
    pdf.multi_cell(0, 5, txt=info_text)

    file_path = "voucher.pdf"
    pdf.output(file_path)
    return file_path

async def generate_voucher_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Начнём создание ваучера. Введите название отеля:")
    context.user_data["voucher_data"] = {}
    return HOTEL_NAME

async def get_hotel_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["voucher_data"]["hotel_name"] = update.message.text
    await update.message.reply_text("Введите адрес отеля:")
    return ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["voucher_data"]["address"] = update.message.text
    await update.message.reply_text("Введите номер телефона отеля:")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["voucher_data"]["phone"] = update.message.text
    await update.message.reply_text("Введите количество ночей (например, 7 nights):")
    return DURATION

async def get_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["voucher_data"]["duration"] = update.message.text
    await update.message.reply_text("Введите дату заезда (например, 21 Mar 2026):")
    return CHECK_IN

async def get_check_in(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["voucher_data"]["check_in"] = update.message.text
    await update.message.reply_text("Введите дату выезда (например, 28 Mar 2026):")
    return CHECK_OUT

async def get_check_out(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["voucher_data"]["check_out"] = update.message.text
    await update.message.reply_text("Введите имена гостей через запятую:")
    return GUEST_INFO

async def get_guest_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["voucher_data"]["guest_info"] = update.message.text
    await update.message.reply_text("Введите тип номера:")
    return ROOM_TYPE

async def get_room_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["voucher_data"]["room_type"] = update.message.text
    await update.message.reply_text("Введите вид из номера:")
    return ROOM_VIEW

async def get_room_view(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["voucher_data"]["room_view"] = update.message.text
    await update.message.reply_text("Введите план питания:")
    return MEAL_PLAN

async def get_meal_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["voucher_data"]["meal_plan"] = update.message.text
    await update.message.reply_text("Введите сумму оплаты (например, 1155$):")
    return AMOUNT_PAID

async def get_amount_paid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["voucher_data"]["amount_paid"] = update.message.text
    data = context.user_data["voucher_data"]
    
    await update.message.reply_text("Генерирую ваучер, подождите...")
    pdf_path = await generate_voucher_pdf(data)
    
    with open(pdf_path, 'rb') as pdf_file:
        await update.message.reply_document(document=pdf_file, filename="voucher.pdf")
    
    await update.message.reply_text("Ваш ваучер готов! Можете начать новый через /generate_voucher")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Создание ваучера отменено.")
    return ConversationHandler.END

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only echo if NOT in a conversation
    await update.message.reply_text(f"Вы написали: {update.message.text}\nДля создания ваучера используйте /generate_voucher")

def main():
    if not TOKEN:
        raise ValueError("TELEGRAM_TOKEN environment variable is not set!")
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    # 1. Conversation Handler (HIGH PRIORITY)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("generate_voucher", generate_voucher_start)],
        states={
            HOTEL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_hotel_name)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_duration)],
            CHECK_IN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_check_in)],
            CHECK_OUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_check_out)],
            GUEST_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_guest_info)],
            ROOM_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_room_type)],
            ROOM_VIEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_room_view)],
            MEAL_PLAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_meal_plan)],
            AMOUNT_PAID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount_paid)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Add handlers in order of priority
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    logger.info("Bot is starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
