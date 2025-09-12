from pydantic import BaseModel

from ..models import LangChoices


class MediaRead(BaseModel):
    imdb_code: str
    lang: LangChoices
