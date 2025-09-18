from pydantic import BaseModel

from ..types import LangChoices


class MediaRead(BaseModel):
    imdb_code: str
    lang: LangChoices
