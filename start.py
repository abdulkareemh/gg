#!/usr/bin/env python3
"""Noor AI — One-command startup script.

Usage:
    python start.py              # Start with SQLite (zero setup)
    python start.py --seed       # Start with demo data
    python start.py --port 9000  # Custom port

The app runs with ZERO external dependencies:
- SQLite for database (no PostgreSQL needed)
- In-memory cache (no Redis needed)
- Rule-based responder (no Claude API needed)
- Console messaging (no WhatsApp API needed)
"""

import argparse
import asyncio
import sys
import os


def check_dependencies():
    """Check that required packages are installed."""
    missing = []
    for pkg in ["fastapi", "uvicorn", "sqlalchemy", "aiosqlite", "pydantic_settings"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"Missing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)


def seed_demo_data():
    """Seed the database with demo data."""
    print("Seeding demo data...")
    from scripts.seed_data import seed
    asyncio.run(seed())
    print("Demo data seeded!")


def print_banner(port: int):
    print()
    print("=" * 50)
    print("  🌟 Noor AI — مساعدك الذكي للأعمال")
    print("=" * 50)
    print()
    print(f"  🌐 App:       http://localhost:{port}")
    print(f"  🎮 Demo:      http://localhost:{port}/demo")
    print(f"  📊 Dashboard: http://localhost:{port}/dashboard")
    print(f"  📚 API Docs:  http://localhost:{port}/docs")
    print(f"  💚 Health:    http://localhost:{port}/health")
    print()
    print("  Database: SQLite (noor.db)")
    print("  Mode:     Development")
    print()
    print("  Press Ctrl+C to stop")
    print("=" * 50)
    print()


def main():
    parser = argparse.ArgumentParser(description="Noor AI — Start the server")
    parser.add_argument("--port", type=int, default=8000, help="Port to run on (default: 8000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--seed", action="store_true", help="Seed demo data before starting")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    # Ensure we're in the right directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    check_dependencies()

    if args.seed:
        # Set SQLite URL before importing app
        os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///noor.db")
        seed_demo_data()

    print_banner(args.port)

    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
