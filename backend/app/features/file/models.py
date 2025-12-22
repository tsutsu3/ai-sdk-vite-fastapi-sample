from pydantic import BaseModel, ConfigDict, Field


class FileResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, frozen=True)

    file_id: str = Field(alias="fileId")
    content_type: str = Field(alias="contentType")
    size: int
