import io
import fitz  # PyMuPDF для PDF
import docx  # для DOCX
from fastapi import UploadFile
from src.core.exceptions import AppError
from loguru import logger

class DocumentParserService:
    @staticmethod
    async def parse(file: UploadFile) -> str:
        """Извлекает текст из загруженного файла в зависимости от его формата."""
        logger.info(f"Начинаем парсинг файла: {file.filename}")
        
        # Считываем файл в оперативную память
        content = await file.read()
        
        # Получаем расширение файла (например, pdf, docx, txt)
        ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''

        try:
            if ext == 'txt':
                return content.decode('utf-8')
                
            elif ext == 'pdf':
                text = ""
                # fitz работает с байтами через stream
                with fitz.open(stream=content, filetype="pdf") as doc:
                    for page in doc:
                        text += page.get_text() + "\n"
                return text.strip()
                
            elif ext == 'docx':
                # python-docx работает с файлоподобными объектами
                doc_file = io.BytesIO(content)
                doc = docx.Document(doc_file)
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
            # Возвращаем указатель файла в начало (на случай, если файл понадобится где-то еще)
            await file.seek(0)

document_parser = DocumentParserService()
