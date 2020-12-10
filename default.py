"""
    Voot Kodi Addon
    Copyright (C) 2018 gujal

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
        elif params['action'] == 'list_extra':
            main.list_extra(params['offSet'])
        elif params['action'] == 'play':
            main.play_video(params['video'],params['quality'] )
        elif params['action'] == 'Live':
            main.list_live(params['offSet'])
    else:
        main.list_top()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
