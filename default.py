"""
    Voot Kodi Addon

"""
import sys
from urlparse import parse_qsl
import xbmcaddon
from resources.lib import main

_addon = xbmcaddon.Addon()
_settings = _addon.getSetting
qualities = ['Tablet Main','TV Main','HLS_TV_HD']
strqual = qualities[int(_settings('quality'))]

def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring:
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin

    if params:
        if params['action'] == 'Channels':
            main.list_channels(params['offSet'])
        elif params['action'] == 'Movies':
            main.list_langs()
        elif params['action'] == 'Clear Cache':
            main.clear_cache()
        elif params['action'] == 'list_channel':
            main.list_shows(params['offSet'],params['channel'],params['totals'])
        elif params['action'] == 'list_movies':
            main.list_movies(params['lang'],params['offSet'],params['totals'])
        elif params['action'] == 'list_season':
            main.list_season(params['show'],params['offSet'],params['totals'])
        elif params['action'] == 'list_show':
            main.list_episodes(params['show'],params['offSet'],params['icon'])
        elif params['action'] == 'play':
            main.play_video(params['video'], strqual)
    else:
        main.list_top()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
