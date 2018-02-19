import re
import os

import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from urllib2 import urlopen, URLError, quote

import json
import datetime
from dateutil.tz import tzlocal
from babel.dates import format_timedelta
from dateutil.parser import parse

def fetch(show=False):
    if show:
        query_string = '?q=' + quote(show) + '&embed[]=previousepisode&embed[]=nextepisode'
        url = 'http://api.tvmaze.com/singlesearch/shows' + query_string
    else:
        url = 'http://api.tvmaze.com/schedule?country=US'

    try:
        resp = utils.web.getUrl(url)
    except utils.web.Error, e:
        return False
    
    data = json.loads(resp)

    return data

class tvmaze(callbacks.Plugin):
    threaded=True

    def tv(self, irc, msg, args, opts, tvshow):
        """[--detail | --rip | --next | --last] <tvshow>

           Command accepts first option only.
        """
        details = False
        rip = False
        next = False
        last = False
        
        print opts
        if opts:
            for (stuff,arg) in opts:
                if stuff == 'detail':
                    details = True
                elif stuff == 'rip':
                    rip = True
                elif stuff == 'next':
                    next = True
                elif stuff == 'last':
                    last = True
                break

        show = fetch(tvshow)

        if show:
            if show['premiered']:
                premiered = show['premiered']
            else:
                premiered = "SOON"

            show_title = ircutils.bold('%s (%s)' % (show['name'], premiered[:4]))

            if "Ended" in show['status']:
                show_state = ircutils.mircColor(show['status'],'red')
            else:
                show_state = ircutils.mircColor(show['status'],'green')
            
            if ( '_embedded' in show and 'previousepisode' in show['_embedded']):
                airtime = parse(show['_embedded']['previousepisode']['airstamp'])
                timedelta = datetime.datetime.now(tzlocal()) - airtime
                relative_time = format_timedelta(timedelta,
                        granularity='minutes')
                last_episode = format('[%s] %s on %s (%s).',
                        ircutils.bold(str(show['_embedded']['previousepisode']['season'])
                            + 'x' +
                            str(show['_embedded']['previousepisode']['number'])),
                        ircutils.bold(show['_embedded']['previousepisode']['name']),
                        ircutils.bold(show['_embedded']['previousepisode']['airdate']),
                        ircutils.mircColor(relative_time, 'red'))
            else:
                last_episode = ''

            if ('_embedded' in show and 'nextepisode' in show['_embedded']):
                airtime = parse(show['_embedded']['nextepisode']['airstamp'])
                timedelta = datetime.datetime.now(tzlocal()) - airtime
                relative_time = format_timedelta(timedelta, granularity='minutes')

                next_episode = format('[%s] %s on %s (%s).',
                        ircutils.bold(str(show['_embedded']['nextepisode']['season'])
                            + 'x' +
                            str(show['_embedded']['nextepisode']['number'])),
                        ircutils.bold(show['_embedded']['nextepisode']['name']),
                        ircutils.bold(show['_embedded']['nextepisode']['airdate']),
                        ircutils.mircColor(relative_time, 'green'))
            else:
                next_episode = 'not yet scheduled'

            
            if rip:
                irc.reply(format('%s is %s', show_title, show_state.upper()))
            elif next:
                if ('_embedded' in show and 'nextepisode' in show['_embedded']):
                    irc.reply(format('%s next scheduled episode is %s', show_title, next_episode))
                else: 
                    if "Ended" in show['status']:
                        irc.reply(format('%s is %s', show_title, show_state.upper()))
                    else:
                        irc.reply(format('%s is %s but does not have a release date for the next episode', show_title, show_state.upper()))
            elif last:
                if ('_embedded' in show and 'previousepisode' in show['_embedded']):
                    irc.reply(format('%s last scheduled episode was %s', show_title, last_episode))
                else:
                    irc.reply(format('%s has not previously run any episodes', show_title))
            else: 
                irc.reply(format('%s [%s] %s:%s %s:%s %s', show_title, show_state, ircutils.underline('Next Episode'), next_episode, ircutils.underline('Previous Episode'), last_episode, show['url']))

        else:
            irc.reply(format('No show found named "%s"', ircutils.bold(tvshow)))

        if details:
            if show['network']:
                show_network = format('%s',
                    ircutils.bold(show['network']['name']))

                show_schedule = format('%s: %s @ %s',
                    ircutils.underline('Schedule'),
                    ircutils.bold(', '.join(show['schedule']['days'])),
                    ircutils.bold(show['schedule']['time']))
            else:
                show_network = format('%s',
                    ircutils.bold(show['webChannel']['name']))

                show_schedule = format('%s: %s',
                    ircutils.underline('Premiered'),
                    ircutils.bold(show['premiered']))

            show_genre = format('%s: %s/%s',
                    ircutils.underline('Genre'),
                    ircutils.bold(show['type']),
                    '/'.join(show['genres']))


            irc.reply(format('%s on %s. %s', show_schedule, show_network,
                show_genre))
        
    tv = wrap(tv, [getopts({'d': '', 'detail': '', 'rip': '', 'next': '', 'last': ''}), 'text'])

    def schedule(self, irc, msg, args):
        """

        """
        shows = fetch(False)
        l = []

        if shows:
            for show in shows:
                if show['show']['type'] == 'Scripted':
                    this_show = format('%s [%s] (%s)',
                            ircutils.bold(show['show']['name']),
                            str(show['season']) + 'x' + str(show['number']),
                            show['airtime'])
                    l.append(this_show)
        
        tonight_shows = ', '.join(l)

        irc.reply(format('%s: %s',
            ircutils.underline("Tonight's Shows"),
            tonight_shows))

                

Class = tvmaze

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
