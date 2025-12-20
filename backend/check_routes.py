#!/usr/bin/env python3
"""Check if webhook routes are registered in FastAPI app."""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Import and create the app (same as server.py)
from dotenv import load_dotenv
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI
from api.v1.webhooks.router import router as webhooks_router

app = FastAPI()
app.include_router(webhooks_router, prefix="/api/v1/webhooks")

# List all routes
print("🔍 Checking registered routes...\n")
print("Webhook routes:")
print("-" * 60)

webhook_routes = [r for r in app.routes if "/webhooks" in str(r.path)]
if webhook_routes:
    for route in webhook_routes:
        methods = ', '.join(route.methods) if hasattr(route, 'methods') else 'N/A'
        print(f"  {methods:10} {route.path}")
    print("\n✅ Webhook routes are registered!")
    print(f"\n📋 Full endpoint: POST /api/v1/webhooks/square")
else:
    print("  ❌ No webhook routes found!")
    print("\nAvailable routes:")
    for route in app.routes:
        methods = ', '.join(route.methods) if hasattr(route, 'methods') else 'N/A'
        print(f"  {methods:10} {route.path}")


