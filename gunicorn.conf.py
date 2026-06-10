import os

port = os.environ.get("PORT", "5000")
bind = f"0.0.0.0:{port}"

workers      = 2
worker_class = "sync"
timeout      = 120
keepalive    = 5
loglevel     = "info"
accesslog    = "-"
errorlog     = "-"
daemon       = False

def on_starting(server):
    """Initialize database before gunicorn starts serving requests."""
    from app import init_db
    init_db()
