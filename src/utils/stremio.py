class StremioStream:
    def __init__(
        self,
        url: str,
        headers: dict | None = None,
        name: str = "",
        title: str = "",
        not_web_ready: bool = False,
        expiry: int | None = None,
        duration: int | None = None,
        source: str | None = None,
    ):
        self.name = name
        self.title = title
        self.url = url
        self.not_web_ready = not_web_ready
        self.expiry = expiry
        self.duration = duration
        self.source = source
        if headers is not None:
            self.headers = headers
        else:
            self.headers = {}
    def to_dict(self):
        behavior_hints = {
            "notWebReady": self.not_web_ready,
            "proxyHeaders": self.headers,
        }
        if self.expiry:
            behavior_hints["expiry"] = self.expiry
        if self.duration:
            behavior_hints["duration"] = self.duration
        if self.source:
            behavior_hints["source"] = self.source

        return {
            "name": self.name,
            "title": self.title,
            "url": self.url,
            "behaviorHints": behavior_hints,
        }


class StremioStreamManager:
    def __init__(self):
        self.streams: list[StremioStream] = []

    def append(self, stream: StremioStream):
        self.streams.append(stream)

    def to_list(self):
        return [stream.to_dict() for stream in self.streams]

    def to_dict(self):
        return {"streams": self.to_list()}
