"""
Обработчик загрузки и обновления тарифов
"""

import os
import tempfile
from aiogram import Router, F
from aiogram.types import Message, Document
from config import is_admin
from utils.tariffs import tariff_manager
from utils.excel_parser import ExcelParser
from utils.logger import bot_logger
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.document)
async def handle_document_upload(message: Message):
    """Обработка загрузки документов (Excel файлов с тарифами)"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Вы не можете обновлять тарифы")
        return
    
    document: Document = message.document
    
    # Проверяем, что это Excel файл
    if not document.file_name.endswith('.xlsx'):
        await message.answer("❌ Поддерживаются только файлы формата .xlsx")
        return
    
    # Проверяем размер файла (максимум 10MB)
    if document.file_size > 10 * 1024 * 1024:
        await message.answer("❌ Размер файла не должен превышать 10MB")
        return
    
    try:
        # Определяем тип файла по названию
        excel_parser = ExcelParser()
        file_type = excel_parser.get_file_type_by_name(document.file_name)
        
        if not file_type:
            await message.answer(
                "❌ Неизвестный тип файла.\n\n"
                "Поддерживаемые файлы:\n"
                "• Комплексная ставка.xlsx\n"
                "• До Новороссийска.xlsx"
            )
            return
        
        # Отправляем сообщение о начале обработки
        processing_msg = await message.answer("⏳ Обрабатываю файл...")
        
        # Скачиваем файл во временную директорию
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            await message.bot.download(document, temp_file.name)
            temp_file_path = temp_file.name
        
        try:
            # Валидируем файл
            is_valid, error_msg = excel_parser.validate_excel_file(temp_file_path, file_type)
            if not is_valid:
                await processing_msg.edit_text(f"❌ Ошибка валидации файла:\n{error_msg}")
                
                # Логируем неудачную загрузку
                bot_logger.log_upload(
                    user_id=message.from_user.id,
                    username=message.from_user.username or "Unknown",
                    upload_data={
                        "filename": document.file_name,
                        "status": "Ошибка валидации",
                        "details": error_msg
                    }
                )
                return
            
            # Обновляем тарифы
            if file_type == "composite":
                result = tariff_manager.update_composite_rates(temp_file_path)
                tariff_type = "комплексных тарифов"
            else:
                result = tariff_manager.update_novorossiysk_rates(temp_file_path)
                tariff_type = "тарифов до Новороссийска"
            
            # Формируем сообщение об успехе
            cities_count = len(result.get("rates", {}))
            valid_until = result.get("valid_until", "Не указано")
            
            success_message = f"✅ <b>Тарифы успешно обновлены</b>\n\n" \
                            f"📁 Файл: {document.file_name}\n" \
                            f"📊 Тип: {tariff_type}\n" \
                            f"🏙 Количество записей: {cities_count}\n" \
                            f"📅 Актуальны до: {valid_until}\n" \
                            f"🕐 Обновлено: {result.get('last_update', '')[:16]}"
            
            if file_type == "composite":
                # Добавляем список городов для комплексных тарифов
                cities = list(result.get("rates", {}).keys())
                if cities:
                    cities_text = ", ".join(cities[:5])
                    if len(cities) > 5:
                        cities_text += f" и еще {len(cities) - 5}"
                    success_message += f"\n🌍 Города: {cities_text}"
            
            await processing_msg.edit_text(success_message, parse_mode='HTML')
            
            # Логируем успешную загрузку
            bot_logger.log_upload(
                user_id=message.from_user.id,
                username=message.from_user.username or "Unknown",
                upload_data={
                    "filename": document.file_name,
                    "status": "Успешно",
                    "details": f"Обновлены {tariff_type}, записей: {cities_count}",
                    "valid_until": valid_until,
                    "file_type": file_type
                }
            )
            
        finally:
            # Удаляем временный файл
            try:
                os.unlink(temp_file_path)
            except:
                pass
    
    except Exception as e:
        logger.error(f"Ошибка обработки файла {document.file_name}: {e}")
        
        error_message = f"❌ <b>Ошибка обработки файла</b>\n\n" \
                       f"📁 Файл: {document.file_name}\n" \
                       f"❗ Ошибка: {str(e)}\n\n" \
                       f"💡 <b>Возможные причины:</b>\n" \
                       f"• Неверная структура файла\n" \
                       f"• Отсутствуют обязательные данные\n" \
                       f"• Файл поврежден\n\n" \
                       f"📞 Обратитесь к разработчику для решения проблемы"
        
        try:
            await processing_msg.edit_text(error_message, parse_mode='HTML')
        except:
            await message.answer(error_message, parse_mode='HTML')
        
        # Логируем ошибку загрузки
        bot_logger.log_upload(
            user_id=message.from_user.id,
            username=message.from_user.username or "Unknown",
            upload_data={
                "filename": document.file_name,
                "status": "Ошибка",
                "details": str(e)
            }
        )

def register_handlers(dp):
    """Регистрация обработчиков"""
    dp.include_router(router) 