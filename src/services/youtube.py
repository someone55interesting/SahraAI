import re
from youtube_transcript_api import YouTubeTranscriptApi
from src.core.exceptions import AppError
from loguru import logger

class YouTubeService:
    @staticmethod
    def extract_video_id(url: str) -> str:
        """Извлекает ID видео из любой ссылки YouTube."""
        pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
        match = re.search(pattern, url)
        if not match:
            logger.error(f"Некорректная ссылка YouTube: {url}")
            raise AppError("Invalid YouTube URL", status_code=400)
        return match.group(1)

    @staticmethod
    def _format_time(seconds: float) -> str:
        """Превращает секунды в формат ЧЧ:ММ:СС или ММ:СС."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    @staticmethod
    def get_transcript(video_id: str, languages=['ru', 'en']) -> str:
        """Получает субтитры и структурирует их по таймкодам в зависимости от длины видео."""
        try:
            ytt_api = YouTubeTranscriptApi()
            transcript_list = ytt_api.fetch(video_id, languages=languages)
            
            if not transcript_list:
                raise AppError("Transcript is empty", status_code=400)

            # Определяем общую длительность видео по последнему элементу
            total_duration = transcript_list[-1].start + transcript_list[-1].duration
            
            # Динамически выбираем шаг группировки текста (в секундах)
            if total_duration < 600:       # Меньше 10 минут
                interval_step = 60         # Группируем каждую 1 минуту
            elif total_duration < 1800:    # Меньше 30 минут
                interval_step = 180        # Группируем каждые 3 минуты
            else:                          # Большие видео (1 час и более)
                interval_step = 300        # Группируем каждые 5 минут

            formatted_blocks = []
            current_interval = interval_step
            current_block_text = []
            
            # Время начала текущего блока
            block_start_time = 0.0

            for item in transcript_list:
                clean_text = item.text.replace('\n', ' ').strip()
                if not clean_text:
                    continue
                
                # Если перешагнули границу интервала, сохраняем блок и начинаем новый
                if item.start >= current_interval:
                    if current_block_text:
                        timestamp = YouTubeService._format_time(block_start_time)
                        formatted_blocks.append(f"[{timestamp}] {' '.join(current_block_text)}")
                    
                    # Смещаем интервал до тех пор, пока он не покроет текущую секунду видео
                    while current_interval <= item.start:
                        current_interval += interval_step
                    
                    block_start_time = item.start
                    current_block_text = [clean_text]
                else:
                    current_block_text.append(clean_text)

            # Не забываем добавить последний оставшийся кусочек текста
            if current_block_text:
                timestamp = YouTubeService._format_time(block_start_time)
                formatted_blocks.append(f"[{timestamp}] {' '.join(current_block_text)}")

            full_text = "\n".join(formatted_blocks)
            
            logger.info(f"Успешно извлечен текст для {video_id}. Блоков: {len(formatted_blocks)}. Длина: {len(full_text)} симв.")
            return full_text
            
        except Exception as e:
            logger.error(f"Ошибка получения субтитров для {video_id}: {str(e)}")
            raise AppError("Could not retrieve subtitles for this video. It might not have them or is restricted.", status_code=400)

youtube_service = YouTubeService()
