"""
    Voot Kodi Addon

"""

import sys
from urlparse import parse_qsl
from urllib import urlencode
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import re
import requests
import math
import uuid
import web_pdb
from json import dumps
try:
    import StorageServer
except:
    import storageserverdummy as StorageServer

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

_addon = xbmcaddon.Addon()
_addonname = _addon.getAddonInfo('name')
_version = _addon.getAddonInfo('version')
_addonID = _addon.getAddonInfo('id')
_icon = _addon.getAddonInfo('icon')
_fanart = _addon.getAddonInfo('fanart')
_settings = _addon.getSetting

cache = StorageServer.StorageServer('voot', _settings('timeout'))

def clear_cache():
    """
    Clear the cache database.
    """
    msg = 'Cached Data has been cleared'
    cache.table_name = 'voot'
    cache.cacheDelete('%get%')
    xbmcgui.Dialog().notification(_addonname, msg, _icon, 3000, False)


if _settings('version') != _version:
    _addon.setSetting('version', _version)
    clear_cache()
    _addon.openSettings()

def refresh_login():
    url = "https://us-central1-vootdev.cloudfunctions.net/usersV3/v3/login"
    #web_pdb.set_trace()
    email=_addon.getSetting('email')
    password = _addon.getSetting('password')
    body = {"type":"traditional","deviceId":"Windows NT 10.0","deviceBrand":"PC/MAC", "data":{"email":email,"password":password}}
    
    body = dumps(body)

    jd = requests.post(url,headers=headers,data=body).json()
    if jd.get('data'):
        headers.update({'refreshToken': jd['data']['authToken']['refreshToken']})
        headers.update({'accessToken': jd['data']['authToken']['accessToken']})
        headers.update({'kToken': jd['data']['kToken']})
        headers.update({'kTokenId': jd['data']['kTokenId']})
        headers.update({'kUserId': jd['data']['kUserId']})
        headers.update({'uId': jd['data']['uId']})
        headers.update({'householdId': str(jd['data']['householdId'])})
        headers.update({'ks': jd['data']['ks']})
    return

apiUrl = 'https://psapi.voot.com/media/voot/v1/'
headers = { #"User-Agent": "okhttp/3.4.1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36",
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br",
            "content-type": "application/json;charset=UTF-8",
            "referer": "https://www.voot.com/",
            "origin":"https://www.voot.com"
          }

refresh_login()

if _settings('EnableIP') == 'true':
    headers['X-Forwarded-For'] = _settings('ipaddress')

sortID = 'sortId=mostPopular'
if _settings('tvsort') == 'Name':
    sortID = 'sortId=a_to_z'

msort = 'sortId=mostPopular'
if _settings('msort') == 'Name':
    msort = 'sortId=a_to_z'

qualities = ['Tablet Main','TV Main','HLS_TV_HD']
strqual = qualities[int(_settings('quality'))]
    

def get_top():
    """
    Get the list of countries.
    :return: list
    """


    MAINLIST = ['Channels', 'Movies','Live', 'Clear Cache']
    return MAINLIST


def get_langs():
    """
    Get the list of languages.
    :return: list
    """
    languages = ['Hindi','Marathi','Telugu','Kannada','Bengali','Gujarati','Tulu']
    #web_pdb.set_trace()
    langs = []
    for item in languages:
        url = '%svoot-web/content/generic/movies-by-language?language=include:%s&sort=title:asc,mostpopular:desc&responseType=common'%(apiUrl,item)

        jd = requests.get(url,headers=headers).json()        
        tcount = jd['totalAsset']
        langs.append((item,tcount))
    
    return langs



def getlicense(id):

    hdr = { "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36",
            "content-type": "application/json",
            "authority": "rest-as.ott.kaltura.com",
            "accept-encoding": "gzip, deflate, br",
            "referer": "https://www.voot.com/",
            "origin":"https://www.voot.com"
          }
    url = "https://rest-as.ott.kaltura.com/v4_4/api_v3/service/multirequest"
    #web_pdb.set_trace()
    token=""
    if headers.get('ks'):
        body = {"1":{"service":"asset","action":"get","id":id,"assetReferenceType":"media","ks":headers['ks']},"2":{"service":"asset","action":"getPlaybackContext","assetId":id,"assetType":"media","contextDataParams":{"objectType":"KalturaPlaybackContextOptions","context":"PLAYBACK"},"ks":headers['ks']},"apiVersion":"5.2.6","ks":headers['ks'],"partnerId":225}
        body = dumps(body)
        jd = requests.post(url,headers=hdr,data=body).json()
        for lictoken in jd['result'][1]['sources']:
            if lictoken.get('type') == 'DASH_LINEAR_APP':
                token=lictoken['drm'][1]['licenseURL']
    return token

def get_channels(offSet):
    """
    Get the list of channels.
    :return: list
    """
    channels = []
    finalpg = True

    url = '%svoot-web/content/specific/editorial?query=include:0657ce8613bb205d46dd8f3c5e7df829&responseType=common&page=%s'%(apiUrl,offSet)

    jd = requests.get(url,headers=headers).json()
    items = jd['result']
    for item in items:
	    title = item.get('name')
	    tcount = item.get('sampledCount')
	    icon = item['seo'].get('ogImage')
	    sbu = item.get('SBU')
	    item_id = item.get('id')
	    channels.append((title, icon, sbu, item_id, tcount))


    offSet = int(offSet)
    totals = int(jd['totalAsset'])
    itemsLeft = totals - offSet * 10
    
    if itemsLeft > 0:
        finalpg = False
        pages = int(math.ceil(totals/10.0))

    if not finalpg:
        title = 'Next Page.. (Currently in Page %s of %s)' % (offSet,pages)
        offSet += 1

        labels = {}
        channels.append((title,_icon,sbu,offSet,tcount))
    return channels


def get_shows(offSet,channel,totals):
    """
    Get the list of shows.
    :return: list
    """
    #web_pdb.set_trace()
    shows = []
    finalpg = True
    url = '%svoot-web/content/generic/shows-by-sbu?sbu=include:%s&sort=mostpopular:desc&&page=%s'%(apiUrl,channel,offSet)
    jd = requests.get(url,headers=headers).json()        
    items = jd['result']
    for item in items:
        title = item.get('name')
        tcount = item['meta'].get('season') if item['meta'].get('season') else 1
        sbu = item['meta'].get('SBU')
        item_id= item.get('id')
        icon = item['details']['image'].get('base')+item['details']['image'].get('id')+'.'+item['details']['image'].get('type')
        labels = {'title': title,
                  'genre': item['meta'].get('genre'),
                  'season': item['meta'].get('season'),
                  'plot': item['meta']['synopsis'].get('full'),
                  'mediatype': 'tvshow',
                  'year': item['meta'].get('releaseYear')}                     
        shows.append((title,icon,sbu,item_id,tcount,labels))

    offSet = int(offSet)
    totals = int(jd['totalAsset'])
    itemsLeft = totals - offSet * 10
    #web_pdb.set_trace()
    if itemsLeft > 0:
        finalpg = False
        pages = int(math.ceil(totals/10.0))

    if not finalpg:
        title = 'Next Page.. (Currently in Page %s of %s)' % (offSet,pages)
        offSet += 1

        labels = {}
        shows.append((title,_icon,sbu,offSet,tcount,labels))

    return shows

def get_season(show,offSet,totals):
    """
    Get the list of episodes.
    :return: list
    """
    season = []
    #web_pdb.set_trace()
    finalpg = True
    url = '%svoot-web/content/generic/season-by-show?sort=season:desc&id=%s&page=%s&responseType=common'%(apiUrl,show,offSet)

    jd = requests.get(url,headers=headers).json()        
    items = jd['result']
    for item in items:
        title = item.get('seasonName')
        item_id = item.get('seasonId')
        icon = item['seo'].get('ogImage')
        sbu=item.get('SBU')
        labels = {'title': title,
                  'genre': item.get('genres'),
                  'plot': item['seo'].get('description'),
                  'cast':item.get('contributors'),
                  'tvshowtitle': item['fullTitle'],
                  'mediatype': 'tvshow',
                  'season': item.get('season')
                 }
        season.append((title,icon,sbu,item_id,labels,totals))

    offSet = int(offSet)
    totals = int(totals)
    itemsLeft = totals - offSet * 10
    #web_pdb.set_trace()
    if itemsLeft > 0:
        finalpg = False
        pages = int(math.ceil(totals/10.0))

    if not finalpg:
        title = 'Next Page.. (Currently in Page %s of %s)' % (offSet,pages)
        offSet += 1

        labels = {}
        season.append((title,_icon,offSet,show,labels,totals))
    return season

	

def get_episodes(show,offSet):
    """
    Get the list of episodes.
    :return: list
    """
    episodes = []
    url = '%svoot-web/content/generic/series-wise-episode?sort=episode:desc&id=%s&&page=%s&responseType=common'%(apiUrl,show,offSet)

    jd = requests.get(url,headers=headers).json()
    totals = jd['totalAsset']
    finalpg = True 
    items = jd['result']
    for item in items:
        title = item['seo'].get('title')
        eid = item.get('id')
        icon={  'poster': item['seo'].get('ogImage'),
                'thumb': item['seo'].get('ogImage'), #'https://v3img.voot.com/resizeMedium,w_175,h_100/'+item.get('image16x9'),
                'icon': item['seo'].get('ogImage'),
                'fanart': item['seo'].get('ogImage')
                    }
        labels = {'title': title,
                  'genre': item.get('genres'),
                  'cast':item.get('contributors'),
                  'plot': item.get('fullSynopsis'),
                  'duration': item['duration'],
                  'tvshowtitle': item['shortTitle'],
                  'mediatype': 'episode',
                  'episode': item.get('episode'),
                  'season': item.get('season'),
                  'aired':item.get('telecastDate')[:4] + '-' + item.get('telecastDate')[4:6] + '-' + item.get('telecastDate')[6:],
                  'year': item.get('releaseYear')
                 }
        #title = 'E%s %s'%(labels.get('episode'), title) if labels.get('episode') else title
        #title = 'S%02d%s'%(int(labels.get('season')), title) if labels.get('season') else title
        #td = item.get('telecastDate')
        #if td:
        #    labels.update({'aired': td[:4] + '-' + td[4:6] + '-' + td[6:]})
        episodes.append((title,icon,eid,labels,totals))

    offSet = int(offSet)
    totals = int(totals)
    itemsLeft = totals - offSet * 10
    #web_pdb.set_trace()
    if itemsLeft > 0:
        finalpg = False
        pages = int(math.ceil(totals/10.0))

    if not finalpg:
        title = 'Next Page.. (Currently in Page %s of %s)' % (offSet,pages)
        offSet += 1

        labels = {}
        episodes.append((title,_icon,offSet,labels,totals))

    return episodes

def get_extra(offSet):
    """
    Get the list of episodes.
    :return: list
    """
    episodes = []
    url = '%svoot-web/content/specific/editorial-clone?query=include:6e5a6d3746fbfb092fd4b090f8505cd8&&page=%s&responseType=common'%(apiUrl,offSet)

    jd = requests.get(url,headers=headers).json()
    totals = jd['totalAsset']
    finalpg = True 
    items = jd['result']
    for item in items:
        title = item['seo'].get('title')
        eid = item.get('id')
        icon={  'poster': item['seo'].get('ogImage'),
                'thumb': item['seo'].get('ogImage'), 
                'icon': item['seo'].get('ogImage'),
                'fanart': item['seo'].get('ogImage')
                    }
        labels = {'title': title,
                  'genre': item.get('genres'),
                  'cast':item.get('contributors'),
                  'plot': item.get('fullSynopsis'),
                  'duration': item['duration'],
                  'tvshowtitle': item['shortTitle'],
                  'mediatype': 'episode',
                  'episode': item.get('episode'),
                  'season': item.get('season'),
                  'aired':item.get('telecastDate')[:4] + '-' + item.get('telecastDate')[4:6] + '-' + item.get('telecastDate')[6:],
                  'year': item.get('releaseYear')
                 }

        episodes.append((title,icon,eid,labels,totals))

    offSet = int(offSet)
    totals = int(totals)
    itemsLeft = totals - offSet * 10

    if itemsLeft > 0:
        finalpg = False
        pages = int(math.ceil(totals/10.0))

    if not finalpg:
        title = 'Next Page.. (Currently in Page %s of %s)' % (offSet,pages)
        offSet += 1

        labels = {}
        episodes.append((title,_icon,offSet,labels,totals))

    return episodes
def get_movies(lang,offSet,totals):
    """
    Get the list of movies.
    :return: list
    """
    movies = []
    totals = int(totals)
    offSet = int(offSet)
    finalpg = True
    itemsLeft = totals - (offSet+1) * 10
    if itemsLeft > 0:
        finalpg = False
        pages = int(math.ceil(totals/10.0))

    url = '%svoot-web/content/generic/movies-by-language?language=include:%s&page=%s&sort=mostpopular:desc&responseType=common'%(apiUrl,lang,offSet)
    jd = requests.get(url,headers=headers).json()        
    items = jd['result']
    #web_pdb.set_trace()
    for item in items:
        title = item.get('name')
        mid = item.get('id')
        icon = item['seo'].get('ogImage')
        labels = {'title': title,
                  'genre': item.get('genres'),
                  'plot': item.get('fullSynopsis'),
                  'cast':item.get('contributors'),
                  'duration':item.get('duration'),   #int(item.get('duration', '0'))/60,
                  'mediatype': 'movie',
                  'mpaa':item.get('age'),
                  'aired':item.get('telecastDate')[:4] + '-' + item.get('telecastDate')[4:6] + '-' + item.get('telecastDate')[6:],
                  'year': item.get('releaseYear')
                 }
        movies.append((title,icon,mid,labels))

    if not finalpg:
        title = 'Next Page.. (Currently in Page %s of %s)' % (offSet,pages)
        offSet += 1
        labels = {}
        movies.append((title,_icon,offSet,labels))

    return movies

def get_live(offSet):
    """
    Get the list of movies.
    :return: list
    """
    live = []

    totals = 40
    offSet = int(offSet)
    finalpg = True
    itemsLeft = totals - (offSet) * 10
    if itemsLeft > 0:
        finalpg = False
        pages = int(math.ceil(totals/10.0))

    url = '%svoot-web/content/specific/editorial?query=include:0657ce8613bb205d46dd8f3c5e7df829&responseType=common&page=%s'%(apiUrl,offSet)
    jd = requests.get(url,headers=headers).json()        
    items = jd['result']
    for item in items:
        title = item.get('name')
        url = '%svoot-web/view/channel/%s?page=1&premiumTrays=false'%(apiUrl,item.get('id'))
        jd = requests.get(url,headers=headers).json()
        newurl=jd['trays'][0]['apiUrl']
        url = '%svoot-web/%s&responseType=common'%(apiUrl,newurl)
        jd = requests.get(url,headers=headers).json()
        mid = jd['result'][0]['id'] if jd['result'] else item.get('id')
        icon = item['seo'].get('ogImage')
        labels = {'title': title,
                  'genre': item.get('genres'),
                  'mediatype': 'movie'
                 }
        live.append((title,icon,mid,labels))

    if not finalpg:
        title = 'Next Page.. (Currently in Page %s of %s)' % (offSet,pages)
        offSet += 1
        labels = {}
        live.append((title,_icon,offSet,labels))

    return live

def list_top():
    """
    Create the list of countries in the Kodi interface.
    """
    items = get_top()

    listing = []
    for item in items:
        list_item = xbmcgui.ListItem(label=item)
        list_item.setInfo('video', {'title': item, 'genre': item})
        list_item.setArt({'icon': _icon,
                          'poster': _icon,
                          'thumb': _icon,
                          'fanart': _fanart})
        url = '{0}?action={1}&offSet=1'.format(_url, item)
        is_folder = True
        listing.append((url, list_item, is_folder))
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.endOfDirectory(_handle)

    
def list_channels(offSet):
    """
    Create the list of countries in the Kodi interface.
    """
    
    channels = cache.cacheFunction(get_channels,offSet)
    listing = []
    for title,icon,sbu,item_id,tcount in channels:
        list_item = xbmcgui.ListItem(label='[COLOR yellow]%s[/COLOR]'%(title))
        list_item.setArt({'poster': icon,
                          'icon': icon,
                          'thumb': icon,
                          'fanart': _fanart})
        list_item.setInfo('video', {'title': title})

        if 'Next Page' not in title:
        	url = '{0}?action=list_channel&offSet=1&channel={1}&totals={2}'.format(_url, sbu, tcount)
        else:
            url = '{0}?action=Channels&offSet={1}&totals={2}'.format(_url, item_id, tcount)
        is_folder = True
        listing.append((url, list_item, is_folder))
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    #xbmcplugin.setContent(_handle, 'videos')
    xbmcplugin.endOfDirectory(_handle)

    
def list_shows(offSet,channel,totals):
    """
    Create the list of channels in the Kodi interface.
    """
    shows = cache.cacheFunction(get_shows,offSet,channel,totals)
    listing = []
    for title,icon,sid,item_id,tcount,labels in shows:
        if 'Next Page' not in title:
            list_item = xbmcgui.ListItem(label='[COLOR yellow]%s  [COLOR cyan](%s Seasons)[/COLOR]'%(title,tcount))
            url = '{0}?action=list_season&offSet=1&show={1}&totals={2}'.format(_url,item_id,tcount)
        else:
            list_item = xbmcgui.ListItem(label='[COLOR yellow]%s[/COLOR]'%(title))
            url = '{0}?action=list_channel&offSet={1}&channel={2}&totals={3}'.format(_url, item_id,sid, tcount)

        
        list_item.setArt({'poster': icon,
                          'thumb': icon,
                          'icon': icon,
                          'fanart': icon})

        list_item.setInfo('video', labels)

        
        is_folder = True
        listing.append((url, list_item, is_folder))
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    #xbmcplugin.setContent(_handle, 'tvshows')
    xbmcplugin.endOfDirectory(_handle)

def list_season(show,offSet,totals):
    """
    Create the list of episodes in the Kodi interface.
    """
    season = cache.cacheFunction(get_season,show,offSet,totals)
    listing = []
    for title,icon,sid,item_id,labels,tcount in season:
        list_item = xbmcgui.ListItem(label=title)
        list_item.setArt({'poster': icon,
                          'thumb': icon,
                          'icon': icon,
                          'fanart': icon})
        list_item.setInfo('video', labels)
        if 'Next Page' not in title:
            url = '{0}?action=list_show&show={1}&offSet={2}&icon={3}'.format(_url,item_id,offSet,icon)
        else:
            url = '{0}?action=list_season&offSet={1}&show={2}&totals={3}'.format(_url,sid,item_id,tcount)

        is_folder = True        
        listing.append((url, list_item, is_folder))
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    #xbmcplugin.setContent(_handle, 'tvshows')
    xbmcplugin.endOfDirectory(_handle)

def list_episodes(show,offSet,sicon):
    """
    Create the list of episodes in the Kodi interface.
    """
    episodes = cache.cacheFunction(get_episodes,show,offSet)
    listing = []
    
    if show == '978245' and offSet == '1':
        list_item = xbmcgui.ListItem(label="Bigboss Extra")
        url = '{0}?action=list_extra&offSet=1'.format(_url)
        is_folder = True 
        listing.append((url, list_item, is_folder))
    
    for title,icon,eid,labels,totals in episodes:
        list_item = xbmcgui.ListItem(label=title)
        list_item.setArt(icon)
        list_item.setInfo('video', labels)
        is_folder = False
        if 'Next Page' not in title:
            list_item.setProperty('IsPlayable', 'true')
            url = '{0}?action=play&video={1}'.format(_url, eid)
        else:
            url = '{0}?action=list_show&show={1}&offSet={2}&totals={3}&icon={4}'.format(_url,show,eid,totals,sicon)
            is_folder = True        
        listing.append((url, list_item, is_folder))
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.setContent(_handle, 'episodes')
    xbmcplugin.endOfDirectory(_handle)

def list_extra(offSet):
    """
    Create the list of episodes in the Kodi interface.
    """
    episodes = cache.cacheFunction(get_extra,offSet)
    listing = []

    for title,icon,eid,labels,totals in episodes:
        list_item = xbmcgui.ListItem(label=title)
        list_item.setArt(icon)
        list_item.setInfo('video', labels)
        is_folder = False
        if 'Next Page' not in title:
            list_item.setProperty('IsPlayable', 'true')
            url = '{0}?action=play&video={1}'.format(_url, eid)
        else:
            url = '{0}?action=list_extra&&offSet={1}'.format(_url,eid)
            is_folder = True        
        listing.append((url, list_item, is_folder))
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.setContent(_handle, 'episodes')
    xbmcplugin.endOfDirectory(_handle)

def list_langs():
    """
    Create the list of countries in the Kodi interface.
    """
    langs = cache.cacheFunction(get_langs)
    listing = []
    for lang,tcount in langs:
        list_item = xbmcgui.ListItem(label='[COLOR yellow]%s  [COLOR cyan](%s movies)[/COLOR]'%(lang,tcount))
        list_item.setInfo('video', {'title': lang, 'genre': lang})
        list_item.setArt({'poster': _icon,
                          'icon': _icon,
                          'thumb': _icon,
                          'fanart': _fanart})
        url = '{0}?action=list_movies&lang={1}&offSet=1&totals={2}'.format(_url, lang, tcount)
        is_folder = True
        listing.append((url, list_item, is_folder))
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.endOfDirectory(_handle)

def list_movies(lang,offSet,totals):
    """
    Create the list of episodes in the Kodi interface.
    """
    movies = cache.cacheFunction(get_movies,lang,offSet,totals)
    listing = []
    for title,icon,mid,labels in movies:
        list_item = xbmcgui.ListItem(label=title)
        list_item.setArt({'poster': icon,
                          'icon': icon,
                          'thumb': icon,
                          'fanart': icon})
        list_item.setInfo('video', labels)
        is_folder = False
        if 'Next Page' not in title:
            list_item.setProperty('IsPlayable', 'true')
            url = '{0}?action=play&video={1}'.format(_url, mid)
        else:
            url = '{0}?action=list_movies&lang={1}&offSet={2}&totals={3}'.format(_url, lang, mid, totals)
            is_folder = True
        listing.append((url, list_item, is_folder))
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.setContent(_handle, 'movies')
    xbmcplugin.endOfDirectory(_handle, succeeded=True, updateListing=True, cacheToDisc=True)


def list_live(offSet):
    """
    Create the list of episodes in the Kodi interface.
    """
    #channels = cache.cacheFunction(get_live,offSet)
    listing=[]

    channels = [(u'Colors Hindi', u'http://v3img.voot.com/v3Storage/channel-logos/COLORS_HINDI.png', u'805985', {'genre': [u'Drama'], 'mediatype': 'movie', 'title': u'Colors Hindi'}),
                (u'BB Live', u'https://v3img.voot.com/resizeMedium,w_362,h_204/v3Storage/assets/BB-24hr%20(6)-1602167714949.jpg', u'998775', {'genre': [u'Drama'], 'mediatype': 'movie', 'title': u'BB Live'}),
                (u'Rishtey Cineplex', u'http://v3img.voot.com/v3Storage/channel-logos/CPR-500x500.png', u'979936', {'genre': [], 'mediatype': 'movie', 'title': u'Rishtey Cineplex'}), 
                (u'MTV', u'http://v3img.voot.com/v3Storage/assets/500x500_1.png', u'805989', {'genre': [u'Reality'], 'mediatype': 'movie', 'title': u'MTV'}),
                (u'MTV Beats', u'http://v3img.voot.com/v3Storage/channel-logos/MTV_BEATS.png', u'805294', {'genre': [u'Music'], 'mediatype': 'movie', 'title': u'MTV Beats'}),
                (u'Colors Marathi', u'http://v3img.voot.com/v3Storage/channel-logos/COLORS_MARATHI.png', u'793930', {'genre': [u'Drama'], 'mediatype': 'movie', 'title': u'Colors Marathi'}),
                (u'Shemaroo TV', u'http://v3img.voot.com/v3Storage/channel-logos/Shemaroo-TV-logo-500x500.png', u'981709', {'genre': [], 'mediatype': 'movie', 'title': u'Shemaroo TV'}),
                (u'Shemaroo Marathi Bana', u'http://v3img.voot.com/v3Storage/channel-logos/MarathiBana_With-tagline-500x500.png', u'981710', {'genre': [], 'mediatype': 'movie', 'title': u'Shemaroo Marathi Bana'}),
                (u'Sonic', u'https://v3img.voot.com/resizeMedium,w_100,h_100/v3Storage/assets/Sonic-1580278480683.jpg', u'708552', {'genre': [u'Education'], 'mediatype': 'movie', 'title': u'Sonic'}),
                (u'Nick Jr', u'https://v3img.voot.com/resizeMedium,w_100,h_100/v3Storage/assets/Nick-Jr-1580292600144.jpg', u'553909', {'genre': [u'Education'], 'mediatype': 'movie', 'title': u'Nick Jr'}),  
                (u'Nick HD+', u'https://v3img.voot.com/resizeMedium,w_100,h_100/v3Storage/assets/Nick-1580278662856.jpg', u'639070', {'genre': [u'Education'], 'mediatype': 'movie', 'title': u'Nick HD+'}),    
                (u'DD National', u'http://v3img.voot.com/v3Storage/channel-logos/DD-national-test.png', u'966639', {'genre': [u'Education'], 'mediatype': 'movie', 'title': u'DD National'}), 
               ]

    for title,icon,mid,labels in channels:
        list_item = xbmcgui.ListItem(label=title)
        list_item.setArt({'poster': icon,
                          'icon': icon,
                          'thumb': icon,
                          'fanart': icon})
        list_item.setInfo('video', labels)
        is_folder = False
        if 'Next Page' not in title:
            list_item.setProperty('IsPlayable', 'true')
            url = '{0}?action=play&video={1}'.format(_url, mid)
        else:
            url = '{0}?action=Live&offSet={1}'.format(_url, mid)
            is_folder = True
        listing.append((url, list_item, is_folder))
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.setContent(_handle, 'movies')
    xbmcplugin.endOfDirectory(_handle)
    



def play_video(path, strqual):
    """
    Play a video by the provided path.

    """

    license=getlicense(path)

    play_item = xbmcgui.ListItem(path=path)
    vid_link = play_item.getfilename()

    url = 'https://apiv2.voot.com/wsv_2_3/playBack.json?mediaId=%s'%(vid_link)
    jd = requests.get(url, headers=headers).json()        
    files = jd['assets'][0]['assets'][0]['items'][0]['files']
    if strqual not in str(files):
        if 'TV Main'  in str(files):
            strqual = 'TV Main'
        elif 'HLS_Linear_P' in str(files):
            strqual = 'HLS_Linear_P'
        else:
            strqual = 'HLS_PremiumHD'

    if license!="":
        for file in files:
            if file.get('Format') == 'DASH_LINEAR_APP':
                stream_url = file.get('URL')
                break
    else:
        for file in files:
            if file.get('Format') == strqual:
                stream_url = file.get('URL') + '|User-Agent=playkit/android-3.4.5 com.tv.v18.viola/2.1.42 (Linux;Android 5.1.1) ExoPlayerLib/2.7.0'
                break

    if _settings('EnableIP') == 'true':
        stream_url += '&X-Forwarded-For=%s'%_settings('ipaddress')

    play_item.setPath(stream_url)

    play_item.setProperty('inputstreamaddon', 'inputstream.adaptive')

    if (stream_url.find('mpd') != -1):
        play_item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        play_item.setMimeType('application/dash+xml')
    else:
        play_item.setProperty('inputstream.adaptive.manifest_type', 'hls')
        play_item.setMimeType('application/vnd.apple.mpegurl')

    if license!="":
        play_item.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
        play_item.setProperty('inputstream.adaptive.license_key', license+ '|%s&Content-Type=application/octet-stream|R{SSM}|' % urlencode(headers))
        play_item.setProperty("inputstream.adaptive.stream_headers", urlencode(headers))
    play_item.setContentLookup(False)
    

    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)

