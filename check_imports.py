"""Check if all modules can be imported"""

try:
    from src.core import TradingPlatform
    print("✓ src.core imports")
except ImportError as e:
    print(f"✗ src.core import error: {e}")

try:
    from src.bots import BaseTradingBot
    print("✓ src.bots imports")
except ImportError as e:
    print(f"✗ src.bots import error: {e}")

try:
    from src.data import MarketData
    print("✓ src.data imports")
except ImportError as e:
    print(f"✗ src.data import error: {e}")

try:
    from src.execution import OrderExecutor
    print("✓ src.execution imports")
except ImportError as e:
    print(f"✗ src.execution import error: {e}")

try:
    from src.risk import RiskManager
    print("✓ src.risk imports")
except ImportError as e:
    print(f"✗ src.risk import error: {e}")

try:
    from src.web.api import app
    print("✓ src.web.api imports")
except ImportError as e:
    print(f"✗ src.web.api import error: {e}")
