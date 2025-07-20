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
    
    'main_menu_buttons': {
        'ai_design': "🎨 طراحی طرح تتو با هوش مصنوعی",
        'book_appointment': "📅 رزرو وقت تتو",
        'contact': "📞 تماس با ما",
        'admin_panel': "👑 پنل مدیریت"
    },
    
    'ai_design_prompt': "لطفاً توضیحات کاملی از طرحی که در ذهن دارید بنویسید:\n\n"
                        "مثال‌ها:\n"
                        "• یک عقاب با بال‌های باز به سبک بلک ورک\n"
                        "• طرح هندسی مثلث‌های متقابل روی مچ دست\n"
                        "• یک جمجمه با چشم‌های درخشان به سبک رئالیسم\n"
                        "• اژدهای آسیایی حول ساعد دست به سبک ترایبال\n"
                        "• کهکشان راه شیری روی پشت دست به سبک دات ورک",
    'ai_design_processing': "در حال ساخت طرح شما... لطفاً چند لحظه صبر کنید.",
    'ai_design_result': "طرح شما آماده شد! ✨\n\nاگر برای اجرای همین طرح وقت رزرو کنید، ۱۰٪ تخفیف ویژه دریافت خواهید کرد.",
    
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
    'api_url': 'https://api.openai.com/v1/images/generations',  # Example endpoint
    'model': 'dall-e-3',
    # Anti-flower bias configuration
    'enable_anti_flower': True,
    'anti_flower_strength': 'medium',  # 'light', 'medium', 'strong'
    'fallback_prompts': True
}

# Scheduler Configuration
SCHEDULER_CONFIG = {
    'reservation_timeout_minutes': 30
}