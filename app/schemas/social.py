from datetime import datetime

from pydantic import BaseModel


class SocialAccountCreate(BaseModel):
    platform: str
    handle: str
    display_name: str | None = None
    profile_url: str | None = None


class SocialAccountUpdate(BaseModel):
    handle: str | None = None
    display_name: str | None = None
    profile_url: str | None = None
    is_active: bool | None = None


class SocialAccountOut(BaseModel):
    id: int
    platform: str
    handle: str
    display_name: str | None
    profile_url: str | None
    is_active: bool
    connected_at: datetime


class SocialAssetOut(BaseModel):
    id: int
    asset_type: str
    prompt: str | None
    provider: str | None
    url: str | None
    status: str
    error: str | None
    created_at: datetime


class SocialPostCreate(BaseModel):
    content: str
    target_platforms: list[str]
    title: str | None = None
    hashtags: list[str] | None = None
    scheduled_at: datetime | None = None
    related_product_id: int | None = None


class SocialPostUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    target_platforms: list[str] | None = None
    hashtags: list[str] | None = None
    scheduled_at: datetime | None = None
    related_product_id: int | None = None
    status: str | None = None  # only for explicit cancellation


class SocialPostOut(BaseModel):
    id: int
    title: str | None
    content: str
    target_platforms: list[str]
    hashtags: list[str]
    status: str
    scheduled_at: datetime | None
    published_at: datetime | None
    ai_generated: bool
    prompt: str | None
    related_product_id: int | None
    related_product_name: str | None = None
    last_error: str | None
    created_at: datetime
    assets: list[SocialAssetOut] = []


class DraftRequest(BaseModel):
    prompt: str
    product_id: int | None = None
    discount_pct: float | None = None
    target_platforms: list[str] | None = None
    template_id: str | None = None


class DraftResponse(BaseModel):
    title: str
    content: str
    hashtags: list[str]
    image_prompt: str
    video_prompt: str
    suggested_platforms: list[str]


class GenerateAssetRequest(BaseModel):
    asset_type: str  # "image" | "video"
    prompt: str
    size: str | None = None  # "1024x1024" gibi
