"""스레드 간 공유 상태. 봇 스레드가 시작된 후 설정됨."""
import asyncio
from typing import Optional

bot_loop: Optional[asyncio.AbstractEventLoop] = None
ptb_app = None  # telegram.ext.Application 인스턴스
