from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from itertools import islice
from typing import Dict, Any, Optional
from fastapi.middleware.cors import CORSMiddleware
from xnxx_api import search_filters
from xnxx_api.xnxx_api import Client as xnxx_client

# Constants
CREATOR = "EyePatch"
API_VERSION = "1.3.0"

# ----- Pydantic Models -----
class SuccessResponse(BaseModel):
    creator: str = CREATOR
    status: str = "success"
    api_version: str = API_VERSION
    data: Dict[str, Any]

class ErrorResponse(BaseModel):
    status: str = "error"
    creator: str = CREATOR
    api_version: str = API_VERSION
    error_code: int
    message: str

class ItemPayload(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tags: list[str] = []

# ----- FastAPI Setup -----
app = FastAPI(title="Awesome API", version=API_VERSION)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- Helper Functions -----
async def get_api_version():
    return API_VERSION

# ----- API Endpoints -----
@app.get("/", response_model=SuccessResponse)
async def root(version: str = Depends(get_api_version)):
    """Service health check endpoint"""
    return SuccessResponse(data={
        "message": "Service operational",
    })

@app.get("/prono/xnxxsearch", response_model=SuccessResponse)
async def xnxx_search(
    query: str,
    quality: Optional[str] = None,
    upload_time: Optional[str] = None,
    length: Optional[str] = None,
    mode: Optional[str] = None,
    page: Optional[int] = None,
    results: Optional[int] = 20
):
    data_dict = {
        "quality": {
            "720p": search_filters.SearchingQuality.X_720p,
            "1080p": search_filters.SearchingQuality.X_1080p_plus
        },
        "upload_time": {
            "year": search_filters.UploadTime.year,
            "month": search_filters.UploadTime.month
        },
        "length": {
            "0-10min": search_filters.Length.X_0_10min,
            "10min+": search_filters.Length.X_10min_plus,
            "10-20min": search_filters.Length.X_10_20min,
            "20min+": search_filters.Length.X_20min_plus
        },
        "mode": {
            "default": search_filters.Mode.default,
            "hits": search_filters.Mode.hits,
            "random": search_filters.Mode.random
        }
    }

    try:
        # Prepare search parameters
        search_kwargs = {
            "query": query
        }
        if length is not None:
            search_kwargs["length"] = data_dict["length"][length]
            
        if quality is not None:
          search_kwargs["searching_quality"] = data_dict["quality"][quality]
            
        if upload_time is not None:
            search_kwargs["upload_time"] = data_dict["upload_time"][upload_time]
            
        if mode is not None:
            search_kwargs["mode"] = data_dict["mode"][mode]
          
        if page is not None:
            search_kwargs["limit"] = page
            
        # Perform the search with only the provided parameters
        search = xnxx_client().search(**search_kwargs)
        res = search.videos
        if results is not None:
            response = islice(res, results)

        results_list = []
        for x in response:
            results_list.append({
                "title": x.title,
                "url": x.url,
                "author": x.author,
                "length": x.length,
                "highest_quality": x.highest_quality,
                "publish_date": x.publish_date,
                "views": x.views,
                "thumb": x.thumbnail_url[0] if isinstance(x.thumbnail_url, list) and len(x.thumbnail_url) > 0 else None
            })
        return SuccessResponse(
            status="True",
            randydev={
                "results": results_list
            }
        )
    except Exception as e:
        return SuccessResponse(
            status="False",
            randydev={"error": f"Error: {e}"}
        )

@app.get("/protected", responses={
    200: {"model": SuccessResponse},
    403: {"model": ErrorResponse}
})
async def protected_route(secret_key: Optional[str] = None):
    """Endpoint demonstrating error responses"""
    if not secret_key or secret_key != "supersecret123":
        return ErrorResponse(
            error_code=403,
            message="Invalid or missing secret key"
        )
    
    return SuccessResponse(data={
        "secret_data": "🔐 You've unlocked premium content!",
        "access_level": "VIP"
    })
