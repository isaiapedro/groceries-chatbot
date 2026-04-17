import os
import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _get_engine():
    password = os.environ.get('DB_PASSWORD')
    if not password:
        try:
            with open('.password', 'r') as f:
                password = f.read().strip()
        except FileNotFoundError:
            raise ValueError("DB_PASSWORD env var or .password file required")

    encoded = urllib.parse.quote_plus(password)
    user = os.environ.get('DB_USER', 'postgres.yahofshjgjxfhogfpxtt')
    host = os.environ.get('DB_HOST', 'aws-1-sa-east-1.pooler.supabase.com')
    port = os.environ.get('DB_PORT', '6543')
    name = os.environ.get('DB_NAME', 'postgres')

    uri = f'postgresql://{user}:{encoded}@{host}:{port}/{name}'
    return create_engine(uri)


engine = _get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
