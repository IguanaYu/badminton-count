from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import SessionLocal, init_db
from .exports.routes import router as exports_router
from .matches.routes import router as matches_router
from .auth.routes import router as auth_router
from .users.routes import router as users_router
from .stats.routes import router as stats_router
from .seed import seed_data

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(matches_router)
app.include_router(stats_router)
app.include_router(exports_router)


@app.on_event("startup")
def on_startup():
    init_db()
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
