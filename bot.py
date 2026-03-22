import os
import logging
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from fpdf import FPDF
from datetime import datetime
from openai import OpenAI

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Credentials
TOKEN = os.environ.get("TELEGRAM_TOKEN")
# OpenAI client is pre-configured with API key and base URL in the environment
client = OpenAI()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать в Hotels Voucher Bot! 🏨\n\n"
        "Пришлите мне любые данные о бронировании (текст, копипаст), и я сразу сделаю PDF-ваучер.\n\n"
        "Я автоматически определю все детали, посчитаю даты и уберу лишние поля (например, цену, если она не указана)."
    )

def clean_text(text):
    """Replace or remove characters that are not supported by standard PDF fonts."""
    if not text: return ""
    # Replace common problematic characters
    replacements = {
        "•": "-",
        "★": "*",
        "–": "-",
        "—": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'"
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Ensure it's latin-1 compatible for standard FPDF fonts
    return text.encode('latin-1', 'replace').decode('latin-1')

async def generate_voucher_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Header
    pdf.set_fill_color(36, 47, 65) # Dark blue
    pdf.rect(0, 0, 210, 30, 'F')
    pdf.set_text_color(255, 255, 255) # White
    pdf.set_font("Helvetica", "B", 16)
    hotel_name = clean_text(data.get("hotel_name", "Hotel Booking"))
    pdf.cell(0, 10, text=hotel_name, ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    conf_num = clean_text(data.get("confirmation", "N/A"))
    pdf.cell(0, 10, text=f"Confirmation Number: {conf_num}", ln=True, align="C")
    pdf.ln(5)

    pdf.set_text_color(0, 0, 0) # Black

    # Sections helper
    def add_section(title, fields):
        if not fields: return
        pdf.set_fill_color(36, 47, 65)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 10, text=title, ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)
        for label, value in fields:
            if value and str(value).lower() != "none" and str(value) != "N/A":
                pdf.cell(40, 7, text=f"{label}:", border=0)
                cleaned_val = clean_text(str(value))
                pdf.cell(0, 7, text=cleaned_val, ln=True)
        pdf.ln(5)

    # 1. Property Info
    prop_fields = []
    if data.get("address"): prop_fields.append(("Address", data["address"]))
    if data.get("phone"): prop_fields.append(("Phone", data["phone"]))
    add_section("PROPERTY INFORMATION", prop_fields)

    # 2. Stay Details
    stay_fields = []
    if data.get("nights"): stay_fields.append(("Duration", data["nights"]))
    if data.get("check_in"): stay_fields.append(("Check-in", data["check_in"]))
    if data.get("check_out"): stay_fields.append(("Check-out", data["check_out"]))
    add_section("STAY DETAILS", stay_fields)

    # 3. Guest Info
    guests_raw = data.get("guest_names", "")
    if guests_raw:
        guest_list = guests_raw.split(",") if "," in guests_raw else guests_raw.split("\n")
        guest_fields = [(f"Guest {i+1}", g.strip()) for i, g in enumerate(guest_list) if g.strip()]
        add_section("GUEST INFORMATION", guest_fields)

    # 4. Room & Services
    room_fields = []
    if data.get("room_name"): room_fields.append(("Room Type", data["room_name"]))
    if data.get("room_view"): room_fields.append(("Room View", data["room_view"]))
    if data.get("meal_plan"): room_fields.append(("Meal Plan", data["meal_plan"]))
    add_section("ROOM & SERVICES", room_fields)

    # 5. Payment Info
    if data.get("price") and str(data["price"]).lower() != "none":
        add_section("PAYMENT INFORMATION", [("Amount Paid", data["price"])])

    # Important Information
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, text="Important Information", ln=True)
    pdf.set_font("Helvetica", "", 10)
    info_text = (
        "- Please present this voucher upon arrival at the hotel.\n"
        "- A valid photo ID and credit card may be required at check-in.\n"
        "- Check-in time is as indicated above. Early check-in is subject to availability.\n"
        "- Late check-out requests should be made directly with the hotel."
    )
    pdf.multi_cell(0, 5, text=info_text)

    file_path = "voucher.pdf"
    pdf.output(file_path)
    return file_path

async def parse_with_ai(text):
    prompt = f"""
    Extract hotel booking information from the following text and return it ONLY as a JSON object.
    If a field is missing, set it to null. 
    Calculate 'nights' if check-in and check-out dates are present.
    Format 'price' with currency if available.
    
    Fields: hotel_name, confirmation, address, phone, check_in, check_out, nights, guest_names, room_name, room_view, meal_plan, price.
    
    Text:
    {text}
    """
    
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text or len(text) < 5:
        return

    await update.message.reply_text("🧠 Анализирую данные...")
    
    try:
        data = await parse_with_ai(text)
        pdf_path = await generate_voucher_pdf(data)
        
        with open(pdf_path, 'rb') as pdf_file:
            hotel_display = data.get('hotel_name') or 'Hotel'
            filename = f"Voucher_{hotel_display.replace(' ', '_')}.pdf"
            await update.message.reply_document(document=pdf_file, filename=filename)
            
        await update.message.reply_text("✨ Готово! Присылайте следующие данные.")
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}. Попробуйте еще раз.")

def main():
    if not TOKEN:
        raise ValueError("TELEGRAM_TOKEN environment variable is not set!")
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Bot is starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
