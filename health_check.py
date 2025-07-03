"""
Health check endpoint for Render deployment
"""
import asyncio
from aiohttp import web
import logging

logger = logging.getLogger(__name__)

async def health_check(request):
    """Simple health check endpoint"""
    return web.json_response({
        'status': 'healthy',
        'service': 'video-encoder-bot'
    })

async def create_health_server():
    """Create health check server"""
    app = web.Application()
    app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    
    logger.info("Health check server started on port 8080")

if __name__ == "__main__":
    asyncio.run(create_health_server())