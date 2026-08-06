import chromadb
from chromadb.utils import embedding_functions
from src.core.exceptions import AppError
from loguru import logger
from src.core.config import settings

class VectorDBService:
    def __init__(self):
        # Сохраняем базу локально в папку
        self.client = chromadb.PersistentClient(path="./chroma_data")
        
        # Подключаем Ollama (с безопасным удалением слэша на конце)
        self.embedding_fn = embedding_functions.OllamaEmbeddingFunction(
            url=f"{settings.OLLAMA_URL.rstrip('/')}/api/embeddings",
            model_name="nomic-embed-text"
        )
        
        # Создаем таблицу (коллекцию)
        self.collection = self.client.get_or_create_collection(
            name="user_documents",
            embedding_function=self.embedding_fn
        )

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += chunk_size - overlap 
        return chunks

    def add_document(self, user_id: int, filename: str, text: str):
        logger.info(f"Подготовка документа {filename} для векторной базы...")
        
        chunks = self.chunk_text(text)
        ids = [f"{user_id}_{filename}_{i}" for i in range(len(chunks))]
        metadatas = [{"user_id": user_id, "filename": filename} for _ in range(len(chunks))]
        
        try:
            logger.info(f"Отправляем {len(chunks)} чанков в ChromaDB...")
            self.collection.add(
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )
            logger.success(f"Документ {filename} успешно сохранен!")
        except Exception as e:
            logger.error(f"Ошибка сохранения в ChromaDB: {e}")
            raise AppError("Failed to save document to vector DB", status_code=500)

    def search(self, user_id: int, query: str, filename: str = None, n_results: int = 3) -> list[dict]:
        """
        Ищет релевантные куски текста.
        Если передан filename, ищет строго в этом файле.
        """
        logger.info(f"Поиск для юзера {user_id}. Файл: {filename}. Запрос: '{query}'")
        
        # Формируем фильтр: если есть filename, ищем строго по нему и юзеру
        if filename:
            where_filter = {
                "$and": [
                    {"user_id": user_id},
                    {"filename": filename}
                ]
            }
        else:
            where_filter = {"user_id": user_id}

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter
            )
            
            formatted_results = []
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
