import tempfile
import os
import shutil
import fitz  # PyMuPDF
import docx  # python-docx
from fastapi import UploadFile
from src.core.exceptions import AppError
from loguru import logger

class DocumentParserService:
    @staticmethod
    async def parse(file: UploadFile) -> str:
        """Извлекает текст, сохраняя файл на диск во временную директорию (защита RAM)."""
        logger.info(f"Начинаем парсинг файла: {file.filename}")
        ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        
        # Создаем временный файл
        fd, temp_path = tempfile.mkstemp(suffix=f".{ext}")
        
        try:
            # Стримим загружаемый файл прямо на диск
            with os.fdopen(fd, 'wb') as tmp:
                shutil.copyfileobj(file.file, tmp)

            # Парсим в зависимости от формата, читая уже с диска
            if ext == 'txt':
                with open(temp_path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
                    
            elif ext == 'pdf':
                text = ""
                with fitz.open(temp_path) as doc:
                    for page in doc:
                        text += page.get_text() + "\n"
                return text.strip()
                
            elif ext == 'docx':
                doc = docx.Document(temp_path)
                return "\n".join([para.text for para in doc.paragraphs]).strip()
                
            else:
                logger.error(f"Неподдерживаемый формат файла: {ext}")
                raise AppError(f"Формат .{ext} пока не поддерживается. Загрузите PDF, DOCX или TXT.", status_code=400)
                
        except AppError:
            raise
        except Exception as e:
            logger.error(f"Ошибка при извлечении текста из {file.filename}: {str(e)}")
            raise AppError("Failed to parse document content", status_code=500)
        finally:
            # Всегда закрываем и удаляем временный файл, освобождая диск
            await file.seek(0)
            if os.path.exists(temp_path):
                os.remove(temp_path)

document_parser = DocumentParserService()
