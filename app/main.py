from fastapi import FastAPI

from app.routers import auth,chat, user

app = FastAPI(
    title="Tecky AI",
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """
    Basic liveness check -- confirms the app is running.
    Does not check DB connectivity; add that later if needed.
    """
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(user.router)
app.include_router(chat.router)