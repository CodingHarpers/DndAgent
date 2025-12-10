from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import routes_play, routes_debug
import uvicorn

app = FastAPI(
    title=settings.APP_NAME,
    description="A.R.C.A.N.A. - Agentic Rules-based & Creative Autonomous Narrative Architecture",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes_play.router, prefix="/api/play", tags=["Play"])
app.include_router(routes_debug.router, prefix="/api/debug", tags=["Debug"])

@app.get("/")
async def root():
    return {"message": "Welcome to A.R.C.A.N.A. System"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
