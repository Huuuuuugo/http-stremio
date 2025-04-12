# functions to extract stream links from site sources

import re

from bs4 import BeautifulSoup
import requests

from .utils import convert_to_punycode
from .decoders import decode_from_response

REDECANAIS_URL = "https://redecanais.ec"
VIDEO_HOST_URL = "https://xn----------------g34l3fkp7msh1cj3acobj33ac2a7a8lufomma7cf2b1sh.xn---1l1--5o4dxb.xn---22--11--33--99--75---------b25zjf3lta6mwf6a47dza94e.xn--pck.xn--zck.xn--0ck.xn--pck.xn--yck.xn-----0b4asja8cbew2b4b0gd0edbjm2jpa1b1e9zva7a0347s4da2797e7qri.xn--1ck2e1b/player3"


def get_video_player_url(video_page_url: str):
    """Extract video url from a given video page, such as the page for a movie or a specific episode of a series."""
    # get video page
    video_page_response = requests.get(video_page_url)
    decoded_video_page = decode_from_response(video_page_response)
    video_page_html = BeautifulSoup(decoded_video_page, "html.parser")

    # get video url
    video_url = ""
    for iframe in video_page_html.find_all("iframe"):
        name = iframe.get("name")
        if name is not None and name == "Player":
            video_url = iframe.get("src")
            video_url = f"{REDECANAIS_URL}{video_url}"

    if video_url:
        return video_url
    else:
        msg = "Failed to extract video url from video page"
        raise Exception(msg)


def get_download_page_url(video_player_url: str):
    """Extract the url to the download page of the given video url"""
    redirect = requests.get(video_player_url, allow_redirects=False)

    # idna encode url to work with requests
    encoded_url = redirect.headers["location"]
    try:
        idna_url = convert_to_punycode(f"https:{encoded_url}")
    except:
        idna_url = encoded_url

    # parse the decoded html to extract serverforms url and token from the decoded html
    response = requests.get(idna_url)
    decoded_html = BeautifulSoup(decode_from_response(response), "html.parser")
    scripts = decoded_html.find_all("script")
    for script in scripts:
        url_match = re.findall(r"url: \'\.(/.+?)\'", script.text)
        if url_match:
            url_match = url_match[0]
            serverforms_url = f"{VIDEO_HOST_URL}{url_match}"
            rctoken = re.findall(r"\'rctoken\':\'(.+?)\'", script.text)[0]

    # request the serverforms url
    serverforms_response = requests.post(serverforms_url, data={"rctoken": rctoken})

    # get download page url from serverforms
    download_page_url = re.findall(r"baixar=\"https://.+?r=(.+?)\"", serverforms_response.text)
    if download_page_url:
        return download_page_url[0]
    else:
        msg = "Could not extract download page url from serverforms html."
        raise Exception(msg)


def get_stream_url(download_page_url: str):
    """Extract the download/stream link from a given download page"""
    # decode download page
    download_page_response = requests.get(download_page_url)
    download_page = decode_from_response(download_page_response)

    # extract download link from download page
    download_link = re.findall(r"const *redirectUrl *= *\'(.+?)\'", download_page)
    if download_link:
        return f"https:{download_link[0]}"
    else:
        msg = "Could not extract download link from download page"
        raise Exception(msg)
