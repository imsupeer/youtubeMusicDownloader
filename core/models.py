from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TrackEntry(BaseModel):
    id: str | None = None
    title: str | None = None
    url: str


class ProbeResult(BaseModel):
    type: Literal["single", "playlist", "unknown"]
    title: str = ""
    entries: list[TrackEntry] = Field(default_factory=list)


class DownloadTask(BaseModel):
    url: str
    bitrate_kbps: int = Field(default=192, ge=128, le=320)
    outdir: str
    filename_template: str = "%(title)s-%(id)s.%(ext)s"
    title: str | None = None

    @field_validator("bitrate_kbps")
    @classmethod
    def normalize_bitrate(cls, value: int) -> int:
        allowed = {128, 192, 256, 320}
        if value not in allowed:
            raise ValueError(f"bitrate_kbps must be one of {sorted(allowed)}")
        return value


class ProbeRequest(BaseModel):
    url: str = Field(min_length=1)


class DownloadRequest(BaseModel):
    outdir: str = Field(min_length=1)
    bitrate_kbps: int = Field(default=192, ge=128, le=320)
    tracks: list[TrackEntry] = Field(min_length=1)


class PickFolderRequest(BaseModel):
    initial_dir: str | None = None


class ProgressEvent(BaseModel):
    type: Literal["progress", "started", "completed", "error", "idle"]
    filename: str = ""
    percent: float = 0.0
    title: str = ""
    message: str = ""
    queue_remaining: int = 0
