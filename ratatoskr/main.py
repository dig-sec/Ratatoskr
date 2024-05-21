import uvicorn

from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException, RequestValidationError

from ratatoskr.routers import query, ingest
from ratatoskr.utils.config import load_config
from ratatoskr.utils.logging import setup_logging
from ratatoskr.utils.dependencies import get_api_key 


# Load your configuration
config = load_config("config.yaml")  
logger = setup_logging(config)

# Create the FastAPI app
app = FastAPI()

# Include Routers (Using Namespaces and API key dependency)
app.include_router(query.router, dependencies=[Depends(get_api_key)])  
app.include_router(ingest.router, dependencies=[Depends(get_api_key)])

# Exception handlers (add more as needed)
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

# Start the app if this file is run directly
if __name__ == "__main__":
    uvicorn.run(app, host=config["host"], port=config["port"])
