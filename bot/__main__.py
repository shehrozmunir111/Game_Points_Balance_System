"""Bot package — allows running with `python -m bot`."""

import asyncio
from bot.bot import main

asyncio.run(main())
