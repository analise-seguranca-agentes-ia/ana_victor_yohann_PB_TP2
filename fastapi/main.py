import sys
from pathlib import Path

# A pasta do projeto se chama "fastapi", o mesmo nome da biblioteca, então não dá
# para transformá-la em pacote (um fastapi/__init__.py esconderia o framework).
# Colocamos a pasta deste arquivo no sys.path para que os imports internos
# funcionem independentemente do diretório de onde a aplicação é executada.
APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import uvicorn
from database import engine
from limiter import limiter
from routes import auth, docs, health, prediction, user
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlmodel import SQLModel

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# As páginas padrão de documentação são desativadas: o /docs é servido por
# routes/docs.py (com SRI e sem script inline) e o /redoc não é utilizado.
app = FastAPI(docs_url=None, redoc_url=None)

SQLModel.metadata.create_all(engine)

# A API só responde JSON, então a política padrão bloqueia qualquer conteúdo.
API_CSP = "default-src 'none'; frame-ancestors 'none'; form-action 'none'; base-uri 'none'"

# O /docs precisa carregar o Swagger UI do CDN (com SRI), o script de
# inicialização da própria API e buscar o /openapi.json.
DOCS_CSP = (
    "default-src 'none'; "
    f"script-src 'self' {docs.SWAGGER_UI_CDN}/; "
    f"style-src {docs.SWAGGER_UI_CDN}/; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; form-action 'self'; base-uri 'none'"
)

allow_origins = ["http://localhost:3000", "http://localhost:8080"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["POST", "GET", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        DOCS_CSP if request.url.path.startswith("/docs") else API_CSP
    )

    return response


app.include_router(docs.docs_router)
app.include_router(auth.auth_router)
app.include_router(user.user_router)
app.include_router(health.health_router)
app.include_router(prediction.prediction_router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app", reload=True, app_dir=str(APP_DIR), reload_dirs=[str(APP_DIR)]
    )
