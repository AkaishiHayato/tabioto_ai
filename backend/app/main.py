from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import cohost, health, listings, sessions

app = FastAPI(title="たびおとAI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(listings.router, prefix="/api/listings", tags=["listings"])
app.include_router(cohost.router, prefix="/api/cohost", tags=["cohost"])
