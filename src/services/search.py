import httpx
from src.core.config import settings
from src.core.exceptions import AppError
from loguru import logger

class WebSearchService:
    @staticmethod
    async def search(query: str, max_results: int = 4) -> str:
        """
        Ищет информацию в интернете через официальный API Tavily.
        """
        logger.info(f"Запрос в Tavily AI по теме: '{query}'")
        
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": settings.TAVILY_API_KEY,
            "query": query,
            "max_results": max_results,
            "include_answer": False # Tavily сам умеет делать краткую выжимку
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=15.0)
                
                if response.status_code != 200:
                    logger.error(f"Ошибка Tavily API: {response.text}")
                    raise AppError("Failed to fetch search results from Tavily", status_code=500)
                    
                data = response.json()
                results = data.get("results", [])
                ai_summary = data.get("answer", "")
                
                if not results and not ai_summary:
                    logger.warning(f"Tavily ничего не нашел по запросу: {query}")
                    return "Нет данных в интернете."

                # Формируем красивый контекст из результатов Tavily
                formatted_results = []
                if ai_summary:
                    formatted_results.append(f"Общая выжимка от поисковика:\n{ai_summary}\n")
                    
                for idx, res in enumerate(results):
                    title = res.get('title', 'Без заголовка')
                    content = res.get('content', '')
                    url_source = res.get('url', '')
                    formatted_results.append(f"[{idx + 1}] {title}\nИсточник: {url_source}\n{content}")
                    
                final_text = "\n\n".join(formatted_results)
                logger.success(f"Tavily успешно нашел {len(results)} источников для '{query}'")
                return final_text

        except Exception as e:
            logger.error(f"Ошибка при запросе к Tavily: {e}")
            raise AppError("Search service internal error", status_code=500)

web_search = WebSearchService()
