import os
import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool


def _get_engine():
    password = os.environ.get("GROCERY_DB_PASSWORD")
    if not password:
        raise ValueError("GROCERY_DB_PASSWORD environment variable is required")

    encoded = urllib.parse.quote_plus(password)
    user = os.environ.get('DB_USER', 'postgres.yahofshjgjxfhogfpxtt')
    host = os.environ.get('DB_HOST', 'aws-1-sa-east-1.pooler.supabase.com')
    port = os.environ.get('DB_PORT', '6543')
    name = os.environ.get('DB_NAME', 'postgres')

    uri = f'postgresql://{user}:{encoded}@{host}:{port}/{name}'
    # NullPool: no idle connections kept alive between requests.
    # Critical for Lambda — prevents connection exhaustion when multiple
    # containers run in parallel, each with their own pool.
    return create_engine(uri, poolclass=NullPool)


engine = _get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
