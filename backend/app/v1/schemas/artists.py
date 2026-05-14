from typing import Optional, List
from pydantic import BaseModel, ConfigDict, model_validator

class ArtistResponse(BaseModel):
    id: str
    name: str
    popularity: Optional[int] = None
    genres: Optional[List[str]] = []
    images: List[dict] = []
    external_urls: dict = {}
    play_count: Optional[int] = None
    rank: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)
    @model_validator(mode="before")
    @classmethod
    def map_fields(cls, data):
        if hasattr(data, "spotify_id"):
            spotify_id = getattr(data, "spotify_id", None)
            image_url = getattr(data, "image_url", None)
            images = [{"url": image_url}] if image_url else []
            return {
                "id": spotify_id,
                "name": getattr(data, "name", ""),
                "popularity": getattr(data, "popularity", None),
                "genres": getattr(data, "genres", []) or [],
                "images": images,
                "external_urls": {"spotify": f"https://open.spotify.com/artist/{spotify_id}"} if spotify_id else {},
                "play_count": getattr(data, "play_count", None),
                "rank": getattr(data, "rank", None),
            }
        return data

class ArtistsResponse(BaseModel):
    artists: List[ArtistResponse]
    total: int
