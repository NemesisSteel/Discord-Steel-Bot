import requests
import config
import html
import re

from plugin import Plugin
from cmd import register, hint, optional, Response
from exceptions import BotException, NotFound
from utils import Embed
from requests.auth import HTTPBasicAuth
from xml.etree import ElementTree
from bs4 import BeautifulSoup
from collections import OrderedDict


def html_parse(string):
    """ Simple html parser for MAL"""
    pattern = '<br[ ]?/?>|\[/?\w\]'
    string = re.sub(pattern, '', string)

    return html.unescape(string)

class Search(Plugin):
    @register('!imgur <search:str>')
    @hint('!imgur [your search]')
    @optional
    def imgur(self, ctx, search):
        url = 'https://api.imgur.com/3/gallery/search/viral'
        headers = {'Authorization': 'Client-ID {}'.format(config.IMGUR_ID)}
        params = {'q': search}
        r = requests.get(url, headers=headers, params=params)
        if r.status_code != 200:
            raise BotException()

        body = r.json()
        data = body.get('data')
        if not data:
            raise NotFound()

        result = data[0]
        message = result['link']

        return Response(message)

    @register('!youtube <search:str>')
    @hint('!youtube [your search]')
    @optional
    def youtube(self, ctx, search):
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {'type': 'video',
                  'q': search,
                  'part': 'snippet',
                  'key': config.GOOGLE_API_KEY}
        r = requests.get(url, params=params)
        if r.status_code != 200:
            raise BotException()

        body = r.json()
        data = body.get('items')
        if not data:
            raise NotFound()

        video = data[0]
        message = 'https://youtu.be/' + video['id']['videoId']

        return Response(message)

    @register('!urban <search:str>')
    @hint('!urban [your search]')
    @optional
    def urban(self, ctx, search):
        url = "http://api.urbandictionary.com/v0/define"
        params = {'term': search}
        r = requests.get(url, params=params)
        if r.status_code != 200:
            raise BotException()

        body = r.json()
        data = body.get('list')
        if not data:
            raise NotFound()

        entry = data[0]

        embed = {'thumbnail': {'url': 'https://upload.wikimedia.org/wikipedia/en/b/b7/Urban_dictionary_--_logo.jpg',
                               'width': 100,
                               'height': 100},
                 'color': 0xCC3C32,
                 'title': entry['word'],
                 'description': entry['definition'],
                 'url': entry['permalink'],
                 'fields': [
                     {'name': 'example',
                      'value': entry['example'],
                      'inline': True},
                 ]}
        embed = Embed(embed)

        return Response(embed=embed)

    @register('!twitch <search:str>')
    @hint('!twitch [streamer name]')
    @optional
    def twitch(self, ctx, search):
        url = "https://api.twitch.tv/kraken/search/channels"
        params = {'q': search,
                  'client_id': config.TWITCH_CLIENT_ID}
        r = requests.get(url, params=params)

        if r.status_code != 200:
            raise BotException()

        body = r.json()
        channels = body.get('channels')
        if not channels:
            raise NotFound()

        channel = channels[0]

        embed = Embed({'color': 0x6441a5,
                       'title': channel['name'],
                       'description': channel['status'],
                       'url': channel['url'],
                       'thumbnail': {'url': channel['logo'],
                                     'width': 100,
                                     'height': 100},
                       'fields': [
                           {'name': 'followers',
                            'value': channel['followers'],
                            'inline': True},
                           {'name': 'views',
                            'value': channel['views'],
                            'inline': True},
                           {'name': 'last played game',
                            'value': channel['game']}
                       ]})

        return Response(embed=embed)

    def mal_resource(self, resource_type, search):
        url = 'https://myanimelist.net/api/' + resource_type + '/search.xml'
        params = {'q': search}
        auth = HTTPBasicAuth(config.MAL_USERNAME, config.MAL_PASSWORD)
        r = requests.get(url, params=params, auth=auth)

        if r.status_code == 204:
            raise NotFound()

        if r.status_code != 200:
            raise BotException()

        body = r.text
        root = ElementTree.fromstring(body)

        entry = root[0]
        fields = ['english',
                  'score',
                  'type',
                  'episodes',
                  'volumes',
                  'chapters',
                  'status',
                  'start_date',
                  'end_date',]

        embed = {'title': entry.find('title').text,
                 'url': 'https://myanimelist.net/{}/{}'.format(resource_type, entry.find('id').text),
                 'description': html_parse(entry.find('synopsis').text),
                 'thumbnail': {'url': entry.find('image').text,
                               'width': 100,},
                 'fields': []}

        for f in fields:
            node = entry.find(f)
            if node is None:
                continue
            value = html.unescape(node.text)
            embed['fields'].append({'name': f.replace('_', ' '),
                                    'value': value,
                                    'inline': True})

        return Response(embed=embed)

    @register('!anime <search:str>')
    @hint('!anime [anime name]')
    @optional
    def manga(self, ctx, search):
        url = 'https://myanimelist.net/api/anime/search.xml'
        params = {'q': search}
        auth = HTTPBasicAuth(config.MAL_USERNAME, config.MAL_PASSWORD)
        r = requests.get(url, params=params, auth=auth)

        if r.status_code == 204:
            raise NotFound()

        if r.status_code != 200:
            raise BotException()

        body = r.text
        root = ElementTree.fromstring(body)

        entry = root[0]
        fields = ['english',
                  'score',
                  'type',
                  'episodes',
                  'volumes',
                  'chapters',
                  'status',
                  'start_date',
                  'end_date',]

        embed = {'title': entry.find('title').text,
                 'url': 'https://myanimelist.net/anime/{}'.format(entry.find('id').text),
                 'description': html_parse(entry.find('synopsis').text),
                 'thumbnail': {'url': entry.find('image').text,
                               'width': 100,},
                 'fields': []}

        for f in fields:
            node = entry.find(f)
            if node is None:
                continue
            value = html.unescape(node.text)
            embed['fields'].append({'name': f.replace('_', ' '),
                                    'value': value,
                                    'inline': True})

        return Response(embed=embed)

    @register('!manga <search:str>')
    @hint('!manga [manga name]')
    @optional
    def manga(self, ctx, search):
        return self.mal_resource('manga', search)

    @register('!anime <search:str>')
    @hint('!anime [anime name]')
    @optional
    def anime(self, ctx, search):
        return self.mal_resource('anime', search)

    @register('!pokemon <search:str>')
    @hint('!pokemon [pokemon name]')
    @optional
    def pokemon(self, ctx, search):
        url = "https://veekun.com/dex/pokemon/search"
        params = {'name': search}
        r = requests.get(url, params=params)

        if r.status_code != 200:
            raise BotException()

        data = r.text
        if 'Nothing found' in data:
            raise NotFound()

        soup = BeautifulSoup(data, "html.parser")
        tds = soup.find_all("td", class_="name")[0].parent.find_all("td")

        name = tds[1].text
        p = OrderedDict()
        p["types"] = ', '.join(map(lambda img: img["title"],
                              tds[2].find_all("img")))
        p["abilities"] = ', '.join(map(lambda a: a.text,
                                  tds[3].find_all("a")))
        p["rates"] = tds[4].find("img")["title"]
        p["egg groups"] = tds[5].text[1:-1].replace("\n", ", ")
        p["hp"] = tds[6].text
        p["atk"] = tds[7].text
        p["def"] = tds[8].text
        p["SpA"] = tds[9].text
        p["SpD"] = tds[10].text
        p["Spd"] = tds[11].text
        p["total"] = tds[12].text
        poke_url = "https://veekun.com" + tds[1].find("a")["href"]

        r = requests.get(poke_url)
        if r.status_code != 200:
            raise BotException()

        data = r.text
        soup2 = BeautifulSoup(data, "html.parser")
        img = soup2.find("div",
                         id="dex-pokemon-portrait-sprite").find("img")
        picture = "https://veekun.com" + img["src"]

        embed = {'color': 0xCC3C32,
                 'url': poke_url,
                 'title': name,
                 'thumbnail': {'url': picture},
                 'fields': []}
        for title, value in p.items():
            embed['fields'].append({'name': title,
                                 'value': value,
                                 'inline': True})

        return Response(embed=embed)
