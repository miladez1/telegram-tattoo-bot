# -*- coding: utf-8 -*-

import logging
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, ConversationHandler
from database import Database
from config import ADMIN_IDS, AI_API_CONFIG, PERSIAN_TEXTS

logger = logging.getLogger(__name__)

# Conversation states
AI_DESIGN_DESCRIPTION = 1
BOOKING_RECEIPT_UPLOAD = 2

db = Database()

def start(update: Update, context: CallbackContext):
    """Start command handler"""
    user = update.effective_user
    
    try:
        db.add_user(user.id, user.first_name, user.username)
    except Exception as e:
        logger.error(f"Error adding user {user.id}: {e}")
    
    # Check forced subscription
    force_channel = db.get_setting('force_join_channel')
    if force_channel:
        try:
            member = context.bot.get_chat_member(force_channel, user.id)
            if member.status in ['left', 'kicked']:
                keyboard = [[InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{force_channel.replace('@', '')}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                update.message.reply_text(
                    "برای استفاده از ربات ابتدا در کانال ما عضو شوید:",
                    reply_markup=reply_markup
                )
                return
        except Exception as e:
            logger.warning(f"Error checking channel membership: {e}")
    
    welcome_message = db.get_setting('welcome_message')
    
    # Get button texts from database
    ai_design_text = db.get_setting('button_ai_design') or PERSIAN_TEXTS['main_menu_buttons']['ai_design']
    book_appointment_text = db.get_setting('button_book_appointment') or PERSIAN_TEXTS['main_menu_buttons']['book_appointment']
    contact_text = db.get_setting('button_contact') or PERSIAN_TEXTS['main_menu_buttons']['contact']
    admin_panel_text = db.get_setting('button_admin_panel') or PERSIAN_TEXTS['main_menu_buttons']['admin_panel']
    
    keyboard = [
        [InlineKeyboardButton(ai_design_text, callback_data='ai_design')],
        [InlineKeyboardButton(book_appointment_text, callback_data='book_appointment')],
        [InlineKeyboardButton(contact_text, callback_data='contact')]
    ]
    
    # Add admin panel button for admins
    if user.id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton(admin_panel_text, callback_data='admin_panel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(welcome_message, reply_markup=reply_markup)

def button_handler(update: Update, context: CallbackContext):
    """Handle inline button presses"""
    query = update.callback_query
    query.answer()
    
    try:
        if query.data == 'ai_design':
            start_ai_design(query, context)
        elif query.data == 'book_appointment':
            show_available_slots(query, context)
        elif query.data == 'book_appointment_discount':
            book_slot_with_discount(query, context)
        elif query.data == 'contact':
            show_contact_info(query, context)
        elif query.data.startswith('book_slot_'):
            slot_id = int(query.data.split('_')[2])
            book_slot(query, context, slot_id)
        elif query.data.startswith('book_discount_'):
            slot_id = int(query.data.split('_')[2])
            book_slot_with_discount(query, context, slot_id)
        elif query.data == 'back_to_main':
            back_to_main_menu(query, context)
        else:
            # Log unhandled callback data for debugging
            logger.warning(f"Unhandled callback data in button_handler: {query.data}")
            
    except Exception as e:
        logger.error(f"Error in button_handler for {query.data}: {e}")
        try:
            query.edit_message_text(
                "خطایی رخ داده است. لطفاً دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_main')]])
            )
        except Exception as edit_e:
            logger.error(f"Error sending error message: {edit_e}")

def start_ai_design(query, context):
    """Start AI design conversation"""
    ai_prompt = db.get_setting('ai_design_prompt') or PERSIAN_TEXTS['ai_design_prompt']
    back_button_text = db.get_setting('back_button') or PERSIAN_TEXTS['back_button']
    
    query.edit_message_text(
        ai_prompt,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(back_button_text, callback_data='back_to_main')]])
    )
    return AI_DESIGN_DESCRIPTION

def handle_ai_design_description(update: Update, context: CallbackContext):
    """Process AI design description"""
    description = update.message.text
    
    # Get configurable messages
    processing_message = db.get_setting('ai_design_processing') or PERSIAN_TEXTS['ai_design_processing']
    result_message = db.get_setting('ai_design_result') or PERSIAN_TEXTS['ai_design_result']
    error_message = db.get_setting('ai_design_error') or PERSIAN_TEXTS['ai_design_error']
    discount_button_text = db.get_setting('booking_discount_button') or PERSIAN_TEXTS['booking_discount_button']
    back_button_text = db.get_setting('back_button') or PERSIAN_TEXTS['back_button']
    
    # Show processing message
    processing_msg = update.message.reply_text(processing_message)
    
    # Call AI API
    try:
        generated_image_path = call_ai_api(description)
        
        if generated_image_path:
            # Delete processing message
            try:
                context.bot.delete_message(
                    chat_id=processing_msg.chat_id,
                    message_id=processing_msg.message_id
                )
            except Exception as e:
                logger.warning(f"Could not delete processing message: {e}")
            
            # Send generated image with discount offer
            keyboard = [[InlineKeyboardButton(discount_button_text, callback_data='book_appointment_discount')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                # Send photo from local file
                with open(generated_image_path, 'rb') as photo_file:
                    update.message.reply_photo(
                        photo=photo_file,
                        caption=result_message,
                        reply_markup=reply_markup
                    )
                
                # Clean up temporary file
                import os
                try:
                    os.unlink(generated_image_path)
                    logger.info(f"Cleaned up temporary file: {generated_image_path}")
                except Exception as e:
                    logger.warning(f"Could not clean up temporary file {generated_image_path}: {e}")
                    
            except Exception as e:
                logger.error(f"Error sending generated image: {e}")
                raise Exception("Error sending image")
        else:
            raise Exception("API call failed")
            
    except Exception as e:
        logger.error(f"AI API error: {e}")
        try:
            processing_msg.edit_text(
                error_message,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(back_button_text, callback_data='back_to_main')]])
            )
        except Exception as edit_e:
            logger.error(f"Could not edit processing message: {edit_e}")
            update.message.reply_text(
                error_message,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(back_button_text, callback_data='back_to_main')]])
            )
    
    return ConversationHandler.END

def call_ai_api(description):
    """Call ClipDrop API to generate tattoo design"""
    api_key = db.get_setting('ai_api_key')
    
    if not api_key:
        logger.error("AI API key not set")
        return None
    
    try:
        # ClipDrop API implementation
        headers = {
            'x-api-key': api_key,
        }
        
        # Prepare the prompt for tattoo design
        tattoo_prompt = f"Black and white tattoo design: {description}, detailed line art, tattoo style, clean lines, professional tattoo artwork"
        
        data = {
            'prompt': tattoo_prompt,
            'width': 512,
            'height': 512,
        }
        
        logger.info(f"Calling ClipDrop API with prompt: {tattoo_prompt}")
        
        response = requests.post(
            AI_API_CONFIG['api_url'], 
            headers=headers, 
            data=data,
            timeout=30
        )
        
        if response.status_code == 200:
            # Save the image temporarily and get URL
            import tempfile
            import os
            
            # Create temporary file
            temp_dir = '/tmp'
            os.makedirs(temp_dir, exist_ok=True)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png', dir=temp_dir) as temp_file:
                temp_file.write(response.content)
                temp_filename = temp_file.name
            
            logger.info(f"ClipDrop API call successful, image saved to: {temp_filename}")
            return temp_filename  # Return local file path for telegram to upload
        else:
            logger.error(f"ClipDrop API error: {response.status_code}, {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error("ClipDrop API call timed out")
        return None
    except requests.exceptions.ConnectionError:
        logger.error("ClipDrop API connection error")
        return None
    except Exception as e:
        logger.error(f"ClipDrop API call failed: {e}")
        return None

def show_available_slots(query, context):
    """Show available appointment slots"""
    slots = db.get_available_slots()
    
    # Get configurable messages
    select_slot_message = db.get_setting('booking_select_slot') or PERSIAN_TEXTS['booking_select_slot']
    no_slots_message = db.get_setting('booking_no_slots') or PERSIAN_TEXTS['booking_no_slots']
    back_button_text = db.get_setting('back_button') or PERSIAN_TEXTS['back_button']
    
    if not slots:
        query.edit_message_text(
            no_slots_message,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(back_button_text, callback_data='back_to_main')]])
        )
        return
    
    keyboard = []
    for slot_id, slot_text in slots:
        keyboard.append([InlineKeyboardButton(slot_text, callback_data=f'book_slot_{slot_id}')])
    
    keyboard.append([InlineKeyboardButton(back_button_text, callback_data='back_to_main')])
    
    query.edit_message_text(
        select_slot_message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def book_slot(query, context, slot_id, discount=False):
    """Book an appointment slot"""
    user_id = query.from_user.id
    
    # Get slot information
    slots = db.get_available_slots()
    slot_text = None
    for sid, stext in slots:
        if sid == slot_id:
            slot_text = stext
            break
    
    # Get configurable messages
    slot_unavailable_message = db.get_setting('booking_slot_unavailable') or PERSIAN_TEXTS['booking_slot_unavailable']
    back_button_text = db.get_setting('back_button') or PERSIAN_TEXTS['back_button']
    cancel_button_text = db.get_setting('cancel_button') or PERSIAN_TEXTS['cancel_button']
    
    if not slot_text:
        query.edit_message_text(
            slot_unavailable_message,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(back_button_text, callback_data='back_to_main')]])
        )
        return
    
    # Create reservation
    try:
        reservation_id = db.create_reservation(user_id, slot_id)
        context.user_data['current_reservation_id'] = reservation_id
        context.user_data['selected_slot_text'] = slot_text
    except Exception as e:
        logger.error(f"Error creating reservation: {e}")
        query.edit_message_text(
            "خطا در ایجاد رزرو. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(back_button_text, callback_data='back_to_main')]])
        )
        return
    
    # Get payment details
    card_number = db.get_setting('card_number')
    card_owner = db.get_setting('card_owner')
    deposit_amount = db.get_setting('deposit_amount')
    
    discount_text = ""
    if discount:
        # Apply 10% discount
        try:
            original_amount = int(deposit_amount)
            discounted_amount = int(original_amount * 0.9)
            deposit_amount = str(discounted_amount)
            discount_text = f"\n🎉 تخفیف ۱۰٪ اعمال شد! (از {original_amount} به {discounted_amount} تومان)"
        except Exception as e:
            logger.error(f"Error calculating discount: {e}")
    
    payment_message = f"""شما زمان {slot_text} را انتخاب کردید.

این زمان به مدت ۲ ساعت برای شما رزرو موقت شد.{discount_text}

برای نهایی کردن رزرو، لطفاً مبلغ بیعانه به مقدار {deposit_amount} تومان را به شماره کارت زیر واریز کرده و از رسید پرداخت اسکرین‌شات بگیرید و ارسال کنید:

💳 شماره کارت: {card_number}
👤 صاحب حساب: {card_owner}

لطفاً اسکرین‌شات رسید را در همین چت ارسال کنید."""
    
    query.edit_message_text(
        payment_message,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{cancel_button_text} رزرو", callback_data='back_to_main')]])
    )
    
    return BOOKING_RECEIPT_UPLOAD

def book_slot_with_discount(query, context, slot_id=None):
    """Book slot with 10% discount after AI design"""
    if slot_id is None:
        # Show available slots for discount booking
        show_available_slots_for_discount(query, context)
    else:
        book_slot(query, context, slot_id, discount=True)

def show_available_slots_for_discount(query, context):
    """Show available slots for discount booking"""
    slots = db.get_available_slots()
    
    # Get configurable messages
    discount_select_message = db.get_setting('booking_discount_select') or PERSIAN_TEXTS['booking_discount_select']
    no_slots_message = db.get_setting('booking_no_slots') or PERSIAN_TEXTS['booking_no_slots']
    back_button_text = db.get_setting('back_button') or PERSIAN_TEXTS['back_button']
    
    if not slots:
        query.edit_message_text(
            no_slots_message,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(back_button_text, callback_data='back_to_main')]])
        )
        return
    
    keyboard = []
    for slot_id, slot_text in slots:
        keyboard.append([InlineKeyboardButton(f"{slot_text} (با ۱۰٪ تخفیف)", callback_data=f'book_discount_{slot_id}')])
    
    keyboard.append([InlineKeyboardButton(back_button_text, callback_data='back_to_main')])
    
    query.edit_message_text(
        discount_select_message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def handle_receipt_upload(update: Update, context: CallbackContext):
    """Handle receipt photo upload"""
    if not update.message.photo:
        receipt_request_message = db.get_setting('booking_receipt_request') or PERSIAN_TEXTS['booking_receipt_request']
        update.message.reply_text(receipt_request_message)
        return BOOKING_RECEIPT_UPLOAD
    
    # Get the largest photo
    photo = update.message.photo[-1]
    reservation_id = context.user_data.get('current_reservation_id')
    
    if not reservation_id:
        error_message = db.get_setting('error_general') or PERSIAN_TEXTS['error_general']
        update.message.reply_text(error_message)
        return ConversationHandler.END
    
    # Save receipt photo ID
    try:
        db.update_reservation_receipt(reservation_id, photo.file_id)
    except Exception as e:
        logger.error(f"Error updating reservation receipt: {e}")
        error_message = db.get_setting('error_general') or PERSIAN_TEXTS['error_general']
        update.message.reply_text(error_message)
        return ConversationHandler.END
    
    # Confirm receipt received
    receipt_received_message = db.get_setting('booking_receipt_received') or PERSIAN_TEXTS['booking_receipt_received']
    update.message.reply_text(receipt_received_message)
    
    # Forward to all admins
    send_receipt_to_admins(context, reservation_id, photo.file_id, update.effective_user)
    
    return ConversationHandler.END

def send_receipt_to_admins(context, reservation_id, photo_file_id, user):
    """Send receipt to all admins for approval"""
    try:
        reservation_data = db.get_reservation_by_id(reservation_id)
        
        if not reservation_data:
            return
        
        _, user_id, slot_id, status, receipt_photo_id, pending_time, created_at, slot_text, first_name, username = reservation_data
        
        # Get configurable admin messages
        admin_caption_template = db.get_setting('admin_receipt_caption') or PERSIAN_TEXTS['admin_receipt_caption']
        approve_button_text = db.get_setting('admin_approve_button') or PERSIAN_TEXTS['admin_approve_button']
        reject_button_text = db.get_setting('admin_reject_button') or PERSIAN_TEXTS['admin_reject_button']
        
        # Format the caption
        caption = admin_caption_template.format(
            first_name=first_name,
            username=username if username else 'بدون نام کاربری',
            user_id=user_id,
            slot_text=slot_text
        )
        
        keyboard = [
            [
                InlineKeyboardButton(approve_button_text, callback_data=f'approve_reservation_{reservation_id}'),
                InlineKeyboardButton(reject_button_text, callback_data=f'reject_reservation_{reservation_id}')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        for admin_id in ADMIN_IDS:
            try:
                context.bot.send_photo(
                    chat_id=admin_id,
                    photo=photo_file_id,
                    caption=caption,
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Failed to send receipt to admin {admin_id}: {e}")
                
    except Exception as e:
        logger.error(f"Error in send_receipt_to_admins: {e}")

def show_contact_info(query, context):
    """Show contact information"""
    contact_info = db.get_setting('contact_info')
    back_button_text = db.get_setting('back_button') or PERSIAN_TEXTS['back_button']
    
    query.edit_message_text(
        contact_info,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(back_button_text, callback_data='back_to_main')]])
    )

def back_to_main_menu(query, context):
    """Return to main menu"""
    user = query.from_user
    welcome_message = db.get_setting('welcome_message')
    
    # Get button texts from database
    ai_design_text = db.get_setting('button_ai_design') or PERSIAN_TEXTS['main_menu_buttons']['ai_design']
    book_appointment_text = db.get_setting('button_book_appointment') or PERSIAN_TEXTS['main_menu_buttons']['book_appointment']
    contact_text = db.get_setting('button_contact') or PERSIAN_TEXTS['main_menu_buttons']['contact']
    admin_panel_text = db.get_setting('button_admin_panel') or PERSIAN_TEXTS['main_menu_buttons']['admin_panel']
    
    keyboard = [
        [InlineKeyboardButton(ai_design_text, callback_data='ai_design')],
        [InlineKeyboardButton(book_appointment_text, callback_data='book_appointment')],
        [InlineKeyboardButton(contact_text, callback_data='contact')]
    ]
    
    # Add admin panel button for admins
    if user.id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton(admin_panel_text, callback_data='admin_panel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(welcome_message, reply_markup=reply_markup)

def handle_reservation_approval(update: Update, context: CallbackContext):
    """Handle admin reservation approval/rejection"""
    query = update.callback_query
    query.answer()
    
    if query.from_user.id not in ADMIN_IDS:
        return
    
    action, reservation_id = query.data.split('_', 1)[0], int(query.data.split('_')[2])
    
    try:
        reservation_data = db.get_reservation_by_id(reservation_id)
        
        if not reservation_data:
            query.edit_message_caption("خطا: رزرو یافت نشد.")
            return
        
        _, user_id, slot_id, status, receipt_photo_id, pending_time, created_at, slot_text, first_name, username = reservation_data
        
        # Get configurable messages
        booking_confirmed_template = db.get_setting('booking_confirmed') or PERSIAN_TEXTS['booking_confirmed']
        booking_rejected_message = db.get_setting('booking_rejected') or PERSIAN_TEXTS['booking_rejected']
        
        if action == 'approve':
            db.confirm_reservation(reservation_id)
            
            # Notify user
            try:
                confirmation_message = booking_confirmed_template.format(slot_text=slot_text)
                context.bot.send_message(
                    chat_id=user_id,
                    text=confirmation_message
                )
            except Exception as e:
                logger.error(f"Failed to notify user {user_id}: {e}")
            
            # Confirm to admin
            query.edit_message_caption(
                caption=f"{query.message.caption}\n\n✅ رزرو تایید شد.",
                reply_markup=None
            )
        
        elif action == 'reject':
            db.reject_reservation(reservation_id)
            
            # Notify user
            try:
                context.bot.send_message(
                    chat_id=user_id,
                    text=booking_rejected_message
                )
            except Exception as e:
                logger.error(f"Failed to notify user {user_id}: {e}")
            
            # Confirm to admin
            query.edit_message_caption(
                caption=f"{query.message.caption}\n\n❌ رزرو رد شد و زمان آن آزاد گردید.",
                reply_markup=None
            )
            
    except Exception as e:
        logger.error(f"Error handling reservation approval: {e}")
        query.edit_message_caption(
            caption=f"{query.message.caption}\n\n❌ خطا در پردازش درخواست.",
            reply_markup=None
        )

def cancel_conversation(update: Update, context: CallbackContext):
    """Cancel current conversation"""
    cancelled_message = db.get_setting('operation_cancelled') or PERSIAN_TEXTS['operation_cancelled']
    update.message.reply_text(cancelled_message)
    return ConversationHandler.END