from services.quotes.repository import QuoteRepository


class QuoteService:
    """
    Business logic layer.
    Currently thin, but allows future expansion
    (permissions, moderation, analytics, etc.)
    """

    def __init__(self):
        self.repo = QuoteRepository()

    async def add_quote(self, *args, **kwargs):
        return await self.repo.add_quote(*args, **kwargs)

    async def get_random_quote(self, *args, **kwargs):
        return await self.repo.get_random_quote(*args, **kwargs)

    async def get_categories(self, *args, **kwargs):
        return await self.repo.get_categories(*args, **kwargs)

    async def delete_quote(self, *args, **kwargs):
        return await self.repo.delete_quote(*args, **kwargs)


quote_service = QuoteService()