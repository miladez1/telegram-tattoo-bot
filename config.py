# -*- coding: utf-8 -*-

# Bot Configuration
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Replace with your actual bot token

# Admin User IDs
ADMIN_IDS = [5574604642, 1487638256]

# Database Configuration
DATABASE_NAME = "tattoo_bot.db"

# Static Persian Texts
PERSIAN_TEXTS = {
    'welcome_message': """🌟 به استودیو تتو خوش آمدید! 🌟

از طریق دکمه‌های زیر می‌توانید:
• طرح تتو خود را با هوش مصنوعی طراحی کنید
• وقت تتو رزرو کنید
• با ما در تماس باشید""",
    
    # Main menu buttons
    'main_menu_buttons': {
        'ai_design': "🎨 طراحی طرح تتو با هوش مصنوعی",
        'book_appointment': "📅 رزرو وقت تتو",
        'contact': "📞 تماس با ما",
        'admin_panel': "👑 پنل مدیریت"
    },
    
    # AI Design messages
    'ai_design_prompt': "لطفاً توضیحات کاملی از طرحی که در ذهن دارید بنویسید (مثلاً: یک شیر با تاج به سبک رئالیسم روی ساعد دست).",
    'ai_design_processing': "در حال ساخت طرح شما... لطفاً چند لحظه صبر کنید.",
    'ai_design_result': "طرح شما آماده شد! ✨\n\nاگر برای اجرای همین طرح وقت رزرو کنید، ۱۰٪ تخفیف ویژه دریافت خواهید کرد.",
    'ai_design_error': "متاسفانه در ساخت طرح مشکلی پیش آمد. لطفاً دوباره تلاش کنید.",
    
    # Booking messages
    'booking_select_slot': "لطفاً یکی از زمان‌های موجود را انتخاب کنید:",
    'booking_no_slots': "متاسفانه در حال حاضر زمانی برای رزرو موجود نیست. لطفاً بعداً تلاش کنید.",
    'booking_slot_unavailable': "متاسفانه این زمان دیگر موجود نیست. لطفاً زمان دیگری انتخاب کنید.",
    'booking_receipt_request': "لطفاً اسکرین‌شات رسید را در همین چت ارسال کنید.",
    'booking_receipt_received': "رسید شما دریافت شد. پس از تایید توسط ادمین، رزرو شما نهایی خواهد شد. لطفاً منتظر بمانید.",
    'booking_confirmed': "✅ رزرو شما برای ساعت {slot_text} با موفقیت تایید و نهایی شد.",
    'booking_rejected': "❌ متاسفانه رزرو شما توسط ادمین رد شد. لطفاً برای رزرو مجدد اقدام کنید.",
    
    # Discount booking
    'booking_discount_select': "لطفاً یکی از زمان‌های موجود را با ۱۰٪ تخفیف انتخاب کنید:",
    'booking_discount_button': "📅 رزرو وقت برای اجرای این طرح (با ۱۰٪ تخفیف)",
    
    # General messages
    'back_button': "🔙 بازگشت",
    'cancel_button': "🔙 لغو",
    'operation_cancelled': "عملیات لغو شد.",
    'error_general': "خطایی رخ داده است. لطفاً دوباره تلاش کنید.",
    
    # Admin messages  
    'admin_receipt_caption': """رسید جدید برای تایید

کاربر: {first_name} (@{username})
شناسه کاربر: {user_id}
زمان انتخابی: {slot_text}""",
    'admin_approve_button': "✅ تایید",
    'admin_reject_button': "❌ رد",
    
    # Bank Details (configurable via admin panel)
    'card_number': "1234-5678-9012-3456",
    'card_owner': "نام صاحب حساب",
    'deposit_amount': "500000",  # in Tomans
    
    # Contact Information
    'contact_info': """📞 اطلاعات تماس:

📱 تلفن: 09123456789
📍 آدرس: تهران، خیابان ولیعصر، پلاک 123
⏰ ساعات کاری: 10:00 تا 22:00"""
}

# AI API Configuration (will be set via admin panel)
AI_API_CONFIG = {
    'api_key': '',
    'api_url': 'https://clipdrop-api.co/text-to-image/v1',  # ClipDrop API endpoint
    'model': 'clipdrop'
}

# Scheduler Configuration
SCHEDULER_CONFIG = {
    'reservation_timeout_minutes': 120  # Changed from 30 to 120 minutes (2 hours)
}