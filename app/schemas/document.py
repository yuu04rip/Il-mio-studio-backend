from pydantic import BaseModel

class DocumentOut(BaseModel):
    id: int
    filename: str
    content_type: str | None = None

    class Config:
        from_attributes = True