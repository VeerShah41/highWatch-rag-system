from contextvars import ContextVar

# This holds the user ID for the current request context
user_id_ctx: ContextVar[str] = ContextVar("user_id", default="default")
