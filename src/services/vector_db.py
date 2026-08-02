import chromadb
from chromadb.utils import embedding_functions
from src.core.exceptions import AppError
from loguru import logger

class VectorDBService:
    def __init__(self):
        # Сохраняем базу локально в папку (она создастся автоматически)
        self.client = chromadb.PersistentClient(path="./chroma_data")
        
        # Подключаем Ollama для перевода текста в векторы
        self.embedding_fn = embedding_functions.OllamaEmbeddingFunction(
            url="http://localhost:11434/api/embeddings",
            model_name="nomic-embed-text"
        )
        
        # Создаем таблицу (коллекцию) для всех документов
        self.collection = self.client.get_or_create_collection(
            name="user_documents",
            embedding_function=self.embedding_fn
        )

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
        """
        Разбивает текст на куски. 
        overlap (перекрытие) нужен, чтобы мысль не обрывалась на стыке двух кусков.
        """
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += chunk_size - overlap 
        return chunks

    def add_document(self, user_id: int, filename: str, text: str):
        """Режет текст на части и сохраняет их в векторную базу."""
        logger.info(f"Подготовка документа {filename} для векторной базы...")
        
        chunks = self.chunk_text(text)
        
        # Генерируем уникальные ID для каждого куска
        ids = [f"{user_id}_{filename}_{i}" for i in range(len(chunks))]
        
        # Метаданные помогут нам потом искать документы конкретного пользователя
        metadatas = [{"user_id": user_id, "filename": filename} for _ in range(len(chunks))]
        
        try:
            logger.info(f"Отправляем {len(chunks)} чанков в ChromaDB (это займет время)...")
            self.collection.add(
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )
            logger.success(f"Документ {filename} успешно сохранен в векторную память!")
        except Exception as e:
            logger.error(f"Ошибка сохранения в ChromaDB: {e}")
            raise AppError("Failed to save document to vector DB", status_code=500)
    def search(self, user_id: int, query: str, n_results: int = 3) -> list[dict]:
        """
        Ищет самые релевантные куски текста по смыслу запроса.
        Строго фильтрует по user_id, чтобы пользователи не читали чужие документы.
        """
        logger.info(f"Поиск по документам юзера {user_id}. Запрос: '{query}'")
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where={"user_id": user_id}  # Защита приватности
            )
            
            formatted_results = []
            # Проверяем, нашла ли база что-нибудь
            if results['documents'] and results['documents'][0]:
                for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                    formatted_results.append({
                        "text": doc,
                        "filename": meta.get("filename", "Неизвестный файл")
                    })
            return formatted_results
            
        except Exception as e:
            logger.error(f"Ошибка поиска в ChromaDB: {e}")
            return []


vector_db = VectorDBService()
