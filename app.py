import requests
import random
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Depends
from itertools import islice
from typing import Optional
from models import SuccessResponse, ErrorResponse, API_VERSION
from fastapi.middleware.cors import CORSMiddleware
from xnxx_api import search_filters
from xnxx_api import Client as xnxx_client
from xvideos_api import Client as xvid_client
from xvideos_api import sorting
from eporner_api import Client as eporner_client, Encoding


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
    
    
async def HentaiAnime():
    try:
        page = random.randint(1, 1153)
        response = requests.get(f'https://sfmcompile.club/page/{page}')
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        hasil = []
        articles = soup.select('#primary > div > div > ul > li > article')
        for article in articles:
            title = article.select_one('header > h2').text
            link = article.select_one('header > h2 > a')['href']
            category = article.select_one('header > div.entry-before-title > span > span').text.replace('in ', '')
            share_count = article.select_one('header > div.entry-after-title > p > span.entry-shares').text
            views_count = article.select_one('header > div.entry-after-title > p > span.entry-views').text
            type_ = article.select_one('source')['type'] if article.select_one('source') else 'image/jpeg'
            video_1 = article.select_one('source')['src'] if article.select_one('source') else article.select_one('img')['data-src']
            video_2 = article.select_one('video > a')['href'] if article.select_one('video > a') else ''
            hasil.append({
                "title": title,
                "link": link,
                "category": category,
                "share_count": share_count,
                "views_count": views_count,
                "type": type_,
                "video_1": video_1,
                "video_2": video_2
            })
        if not hasil:
            return {'developer': '@neomatrix90', 'error': 'no result found'}
        return hasil
    except Exception:
        return None    

# ----- API Endpoints -----
@app.get("/", response_model=SuccessResponse)
async def root(version: str = Depends(get_api_version)):
    """Service health check endpoint"""
    return SuccessResponse(data={
        "message": "Service operational",
    })
    
    
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
    

@app.get("/prono/xnxxsearch", response_model=SuccessResponse)
async def xnxx_search(
    query: str,
    quality: Optional[str] = None,
    upload_time: Optional[str] = None,
    length: Optional[str] = None,
    mode: Optional[str] = None,
    # page: Optional[int] = None,
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
          
        # if page is not None:
            # search_kwargs["limit"] = page
            
        # Perform the search with only the provided parameters
        c = xnxx_client()
        search = c.search(**search_kwargs)
        # response = search.videos
        # if results is not None:
            # response = islice(res, results)

        results_list = []
        for x in islice(search.videos, results):
            results_list.append({
                "title": x.title,
                "url": x.url,
                "author": x.author,
                "length": x.length,
                # "highest_quality": x.highest_quality,
                "publish_date": x.publish_date,
                # "views": x.views,
                "thumb": x.thumbnail_url[0] if isinstance(x.thumbnail_url, list) and len(x.thumbnail_url) > 0 else None
            })
        return SuccessResponse(
            data={
                "results": results_list
            }
        )
    except Exception as e:
        return SuccessResponse(
            status="False",
            data={"error": f"Error: {e}"}
        )
    
    
@app.get("/prono/hentai", response_model=SuccessResponse)
async def hentai_():
    try:
        response = await HentaiAnime()
        return SuccessResponse(
            status="True",
            data={"results": response}
        )
    except:
        return SuccessResponse(
            status="False",
            data={"error": "Error fucking"}
        )    


@app.get("/prono/xnxx-dl", response_model=SuccessResponse, responses={422: {"model": SuccessResponse}})
async def xnxx_download(link: str):
    try:
        x = xnxx_client()
        response = x.get_video(link)
        return SuccessResponse(
            data={
                "results": {
                    "title": response.title,
                    "author": response.author,
                    "length": f"{response.length} min",
                    "highest_quality": response.highest_quality,
                    "publish_date": response.publish_date,
                    "views": response.views,
                    "link": response.content_url,
                    "thumb": response.thumbnail_url[0] if isinstance(response.thumbnail_url, list) and len(response.thumbnail_url) > 0 else None
                }
            }
        )

    except Exception as e:
        return SuccessResponse(
            status="False",
            randydev={"error": f"Error fucking: {e}"}
        )


@app.get("/prono/xvidsearch", response_model=SuccessResponse)
async def xvid_search(
    query: str,
    quality: Optional[str] = None,
    upload_time: Optional[str] = None,
    length: Optional[str] = None,
    mode: Optional[str] = None,
    # page: Optional[int] = None,
    results: Optional[int] = 20
):
    data_dict = {
        "quality": {
            "720p": sorting.SortQuality.Sort_720p,
            "1080p": sorting.SortQuality.Sort_1080_plus
        },
        "upload_time": {
            "3months": sorting.SortDate.Sort_last_3_months,
            "6months": sorting.SortDate.Sort_last_6_months
        },
        "length": {
            "0-10min": sorting.SortVideoTime.Sort_middle,
            "10min+": sorting.SortVideoTime.Sort_long,
            "10-20min": sorting.SortVideoTime.Sort_long_10_20min,
            "20min+": sorting.SortVideoTime.Sort_really_long
        },
        "mode": {
            "rating": sorting.Sort.Sort_rating,
            "views": sorting.Sort.Sort_views,
            "random": sorting.Sort.Sort_random,
            "relevance": sorting.Sort.Sort_relevance
        }
    }

    try:
        # Prepare search parameters
        search_kwargs = {
            "query": query
        }
        if length is not None:
            search_kwargs["sorting_time"] = data_dict["length"][length]
            
        if quality is not None:
          search_kwargs["sort_quality"] = data_dict["quality"][quality]
            
        if upload_time is not None:
            search_kwargs["sorting_time"] = data_dict["upload_time"][upload_time]
            
        if mode is not None:
            search_kwargs["sorting_sort"] = data_dict["mode"][mode]
          
            
        # Perform the search with only the provided parameters
        c = xvid_client()
        search = c.search(**search_kwargs)
        # response = search.videos
        # if results is not None:
            # response = islice(res, results)

        results_list = []
        for x in islice(search, results):
            results_list.append({
                "title": x.title,
                "url": x.url,
                "author": x.author,
                "length": x.length,
                "publish_date": x.publish_date,
                "views": x.views,
                "thumb": x.thumbnail_url
            })
        return SuccessResponse(
            data={
                "results": results_list
            }
        )
    except Exception as e:
        return SuccessResponse(
            status="False",
            data={"error": f"Error: {e}"}
        )


@app.get("/prono/xvid-dl", response_model=SuccessResponse, responses={422: {"model": SuccessResponse}})
async def xvid_download(link: str):
    try:
        x = xvid_client()
        response = x.get_video(link)
        return SuccessResponse(
            data={
                "results": {
                    "title": response.title,
                    "description": response.description,
                    "author": response.author,
                    "length": response.length,
                    "tags": response.tags,
                    "publish_date": response.publish_date,
                    "views": response.views,
                    "link": response.cdn_url,
                    "thumb": response.thumbnail_url
                }
            }
        )

    except Exception as e:
        return SuccessResponse(
            status="False",
            randydev={"error": f"Error fucking: {e}"}
        )
        
        
# --- Eporner Search Endpoint ---
@app.get("/prono/epornersearch", response_model=SuccessResponse)
async def eporner_search(
    query: str,
    page: Optional[int] = 0,
    per_page: Optional[int] = 20,
    sorting_order: Optional[str] = None,
    sorting_gay: Optional[bool] = False,
    sorting_low_quality: Optional[bool] = False,
):
    try:
        client = eporner_client()
        # Set sorting options if provided
        search_kwargs = {
            "query": query,
            "page": page,
            "per_page": per_page
            # "sorting_gay": sorting_gay,
            # "sorting_low_quality": sorting_low_quality
        }

        if sorting_order:
            from eporner_api.modules.sorting import Order
            order_map = {
                "newest": Order.newest,
                "longest": Order.longest,
                "top_rated": Order.top_rated,
                "most_viewed": Order.most_viewed
            }
            search_kwargs["sorting_order"] = order_map.get(sorting_order)

        results_list = []
        for video in client.search_videos(**search_kwargs):
            results_list.append({
                "title": video.title,
                "url": video.url,
                "length": video.length,
                "views": video.views,
                "rate": video.rate,
                "publish_date": video.publish_date,
                "thumbnail": video.thumbnail,
                "tags": video.tags,
                "pornstars": video.pornstars,
                "embed_url": video.embed_url
            })
        return SuccessResponse(
            data={"results": results_list}
        )

    except Exception as e:
        return SuccessResponse(
            status="False",
            data={"error": f"Search failed: {e}"}
        )