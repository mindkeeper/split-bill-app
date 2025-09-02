"""Legacy main.py - redirects to new app structure"""

# Import the new FastAPI app
from app.main import app

# Re-export the app for backward compatibility
__all__ = ["app"]