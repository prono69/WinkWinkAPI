import requests
import random
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import time
import asyncio
import datetime
from itertools import islice
from typing import Optional
from models import SuccessResponse, ErrorResponse, API_VERSION
from fastapi.middleware.cors import CORSMiddleware
from xnxx_api import search_filters
from xnxx_api import Client as xnxx_client
from xvideos_api import Client as xvid_client
from xvideos_api import sorting
from eporner_api import Client as eporner_client, sorting as eporner_sort
from hqporner_api import Client as hqporner_client


# ----- FastAPI Setup -----
app = FastAPI(title="Cultured API", version=API_VERSION)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")
SERVER_START_TIME = datetime.datetime.utcnow()

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

# Safe attribute getter
def safe_get(obj, attr, default="Not available"):
    return getattr(obj, attr, default)
    
def format_uptime(start_time):
    delta = datetime.datetime.utcnow() - start_time
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if days:
        parts.append(f"{days} day{'s' if days > 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
    if not parts:
        parts.append(f"{seconds} seconds")
    return ", ".join(parts)
    
# Mount static folder
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve favicon
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(os.path.join("static", "favicon.ico"))

# ----- API Endpoints -----

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("preview.html", {
        "request": request,
        "title": "Cultured API",
        "description": "A NSFW Fast API to Search/Download videos from some sources. Comes with Swagger UI.",
        "image_url": "https://files.catbox.moe/pwr4s2.jpg",
        "url": "https://napi.ichigo.eu.org/"
    })

@app.get("/check", response_model=SuccessResponse)
async def health_check(version: str = Depends(get_api_version)):
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

    
@app.get("/ping", response_model=SuccessResponse)
async def ping_check():
    start_time = time.perf_counter()
    await asyncio.sleep(0)
    end_time = time.perf_counter()
    latency_ms = round((end_time - start_time) * 1000, 2)

    if latency_ms < 50:
        message = "⚡ Super fast! Everything’s snappy!"
        level = "green"
        rank = 3
    elif latency_ms < 150:
        message = "🚀 Fast! Good response time."
        level = "lightgreen"
        rank = 2
    elif latency_ms < 300:
        message = "🚦 Moderate speed. Not bad."
        level = "yellow"
        rank = 1
    elif latency_ms < 600:
        message = "🐢 A bit slow. Could be better."
        level = "orange"
        rank = 0
    else:
        message = "🐌 Very slow. Time to wake up the servers!"
        level = "red"
        rank = -1

    uptime = format_uptime(SERVER_START_TIME)

    return SuccessResponse(data={
        "ping": f"{latency_ms} ms",
        "message": message,
        "status_level": level,
        "status_rank": rank,
        "uptime": uptime
    })
    
# --- Xnxx Search Endpoint ---
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
    
# --- Random Hentai Endpoint ---
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

# --- Xnxx Download Info ---
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


# --- Xvideos Search Endpoint ---
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


# --- Xvideos Download Info ---
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
    sorting_order: Optional[str] = "latest",
    sorting_gay: Optional[str] = "0",
    sorting_low_quality: Optional[str] = "0",
    page: Optional[int] = 0,
    per_page: Optional[int] = 10,
):
    try:
        # Validate and resolve sorting order
        if sorting_order not in {
            eporner_sort.Order.latest,
            eporner_sort.Order.longest,
            eporner_sort.Order.shortest,
            eporner_sort.Order.top_rated,
            eporner_sort.Order.most_popular,
            eporner_sort.Order.top_weekly,
            eporner_sort.Order.top_monthly
        }:
            raise ValueError(f"Invalid sorting_order: {sorting_order}")

        if sorting_gay not in {
            eporner_sort.Gay.exclude_gay_content,
            eporner_sort.Gay.include_gay_content,
            eporner_sort.Gay.only_gay_content
        }:
            raise ValueError(f"Invalid sorting_gay: {sorting_gay}")

        if sorting_low_quality not in {
            eporner_sort.LowQuality.exclude_low_quality_content,
            eporner_sort.LowQuality.include_low_quality_content,
            eporner_sort.LowQuality.only_low_quality_content
        }:
            raise ValueError(f"Invalid sorting_low_quality: {sorting_low_quality}")

        client = eporner_client()

        videos = client.search_videos(
            query,
            sorting_gay,
            sorting_order,
            sorting_low_quality,
            page,
            per_page
        )

        results_list = []
        for video in videos:
            results_list.append({
                "id": video.video_id,
                "title": video.title,
                "url": video.link,
                "length": video.length,
                "length_minutes": video.length_minutes,
                "views": video.views,
                "rate": video.rate,
                "publish_date": video.publish_date,
                "thumbnail": video.thumbnail,
                "tags": video.tags,
            })

        return SuccessResponse(data={"results": results_list})

    except Exception as e:
        return SuccessResponse(
            status="False",
            data={"error": f"Search failed: {e}"}
        )
        
        
# --- Eporner Download Info ---
@app.get("/prono/eporner-dl", response_model=SuccessResponse)
async def eporner_download(link: str):
    try:
        client = eporner_client()
        video = client.get_video(link, enable_html_scraping=True)

        return SuccessResponse(
            data={
                "results": {
                    "title": safe_get(video, "title"),
                    # "description": safe_get(video, "html_content"),
                    "author": safe_get(video, "author"),
                    "length": safe_get(video, "length"),
                    "length_minutes": safe_get(video, "length_minutes"),
                    "views": safe_get(video, "views"),
                    "rate": safe_get(video, "rate"),
                    # "rate_count": safe_get(video, "rating_count"),
                    "publish_date": safe_get(video, "publish_date"),
                    "tags": safe_get(video, "tags", []),
                    "likes": safe_get(video, "likes"),
                    "dislikes": safe_get(video, "dislikes"),
                    "source_url": safe_get(video, "source_video_url"),
                    "bitrate": safe_get(video, "bitrate"),
                    # "download_link": video.download(quality="best", path="./", mode=Encoding.mp4_h264),
                    "thumbnail": safe_get(video, "thumbnail")
                }
            }
        )

    except Exception as e:
        return ErrorResponse(
            error_code=500,
            message=f"Download info failed: {e}"
        )
        
        
# --- HQPorner Search Endpoint ---
@app.get("/prono/hqpornersearch", response_model=SuccessResponse)
async def hqporner_search(
    query: str,
    pages: Optional[int] = 1,
    limit: Optional[int] = 10
):
    try:
        client = hqporner_client()
        videos = client.search_videos(query, pages=pages)

        results_list = []
        for video in islice(videos, limit):
            results_list.append({
                "title": safe_get(video, "title"),
                "url": safe_get(video, "url"),
                "length": safe_get(video, "length"),
                "pornstars": safe_get(video, "pornstars", []),
                "publish_date": safe_get(video, "publish_date"),
                "tags": safe_get(video, "tags", [])
            })

        return SuccessResponse(data={"results": results_list})

    except Exception as e:
        # Technically this should return ErrorResponse, but preserving your original style
        return SuccessResponse(
            status="error",
            data={"error": f"HQPorner search failed: {e}"}
        )