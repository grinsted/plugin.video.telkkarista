#kodi telkkarista plugin
# This Python file uses the following encoding: utf-8
#
# This plugin is modelled over the now defunct TVKaista plugin. 
# Ackownledgements goes to Viljo Viitanen,sampov2,stilester,& J. Luukko
#
# Copyright (C) 2015       Aslak Grinsted
# Copyright (C) 2009-2014  Viljo Viitanen <viljo.viitanen@iki.fi>
# Copyright (C) 2014       grinsted
# Copyright (C) 2014       sampov2
# Copyright (C) 2010       stilester
# Copyright (C) 2008-2009  J. Luukko
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.#
#
# change history:
#
#
# Github: https://github.com/grinsted/plugin.video.telkkarista
# 
# Aslak Grinsted 2015 


VERSION = "0.0.1"

import xbmc, xbmcgui, requests, json, re, os, xbmcplugin, urllib, time, xbmcaddon
import datetime, urlparse, random
import dateutil.parser, dateutil.tz
telkkarista_addon = xbmcaddon.Addon("plugin.video.telkkarista");
language = telkkarista_addon.getLocalizedString

BASE_RESOURCE_PATH = xbmc.translatePath( os.path.join( telkkarista_addon.getAddonInfo('path'), "resources" ) )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

from string import split, replace, find

APIROOT='http://api.telkkarista.com/1/'
PLAYROOT=telkkarista_addon.getSetting("currentcachehost") #the selected server. Will be chosen at every login...
sessionkey=telkkarista_addon.getSetting("sessionkey")


def login():
  global PLAYROOT
  global sessionkey
  headers = {'User-Agent': "telkkarista for kodi version "+VERSION+";"}
  data={'email': telkkarista_addon.getSetting("username"), 'password': telkkarista_addon.getSetting("password")}
  response=requests.post(url=APIROOT+'user/login',data=json.dumps(data),headers=headers)
  response=response.json()
  sessionkey=response['payload']
  xbmc.log('TELKKARISTA LOGIN! %s' % (sessionkey))
  telkkarista_addon.setSetting("sessionkey",sessionkey)
  preferredhosts=telkkarista_addon.getSetting("preferredhosts").split(',')
  #if not preferredhosts: speedtest()
  servers=apiget('cache/get','',False)
  servers=dict((s['host'], s['country']) for s in servers if s['status']=='up')
  if len(servers)==0:
    xbmcgui.dialog.ok(" All cache servers are down! ")
    return
  for host in preferredhosts:
    if host in servers:
      PLAYROOT=host
      telkkarista_addon.setSetting("currentcachehost",host) #Found preferredhost
      return
  PLAYROOT=servers.keys()[0]
  telkkarista_addon.setSetting("currentcachehost",PLAYROOT)


def apiget(url,data='',allowrecursion=True):
  global sessionkey
  xbmc.log(sessionkey)
  if sessionkey=='': login()
  headers = {'X-SESSION': sessionkey, 'User-Agent': "telkkarista for kodi version "+VERSION+";"}
  if not isinstance(data, basestring):
    data = json.dumps(data)
  response=requests.post(url=APIROOT+url,data=data,headers=headers)
  #TODO add checks for response errors....
  response=response.json()
  #if key expired:
  if response['status'] == 'error':
    xbmc.log('telkkarista apiget error' % (repr(response)))
    if response['code'] == 'invalid_session':
      if allowrecursion:
        xbmc.log('Telkkarista invalid session - logging in...')
        login()
        return apiget(url=url,data=data,allowrecursion=False)
  return response['payload']


#display settings if username and password are not set
def settings():
  if telkkarista_addon.getSetting("username") != '' and telkkarista_addon.getSetting("password") != '':
    menu()
  else:
    u=sys.argv[0]+"?mode=settings"
    listfolder = xbmcgui.ListItem('-- '+language(30201)+' --') #Asetuksia ei määritelty tai niissa on ongelma. Tarkista asetukset.
    listfolder.setInfo('video', {'Title': language(30201)})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
    u=sys.argv[0]+"?mode=settings"
    listfolder = xbmcgui.ListItem(language(30101)) #asetukset
    listfolder.setInfo('video', {'Title': language(30101)})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))




# paavalikko
def menu():
  t2=datetime.datetime.now()
  t1=t2 - datetime.timedelta(days=1)
  data = json.dumps({"from":t1.isoformat(), "to":t2.isoformat()})
  u=sys.argv[0]+"?mode=listprograms&url=epg/range&data="+requests.utils.quote(data)
  listfolder = xbmcgui.ListItem(language(30102)) #'Kanavat - tänään'
  listfolder.setInfo('video', {'Title': language(30102)})
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  data = json.dumps({"search":'elokuva'});
  u=sys.argv[0]+"?mode=listprograms&url=epg/search&data="+requests.utils.quote(data)
  listfolder = xbmcgui.ListItem(language(30105)) #movies
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  u=sys.argv[0]+"?mode=listsearches"
  listfolder = xbmcgui.ListItem(language(30106)) #haku
  listfolder.setInfo('video', {'Title': language(6)})
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  u=sys.argv[0]+"?mode=live"
  listfolder = xbmcgui.ListItem(language(30107)) #live tv
  listfolder.setInfo('video', {'Title': language(30107)})
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  u=sys.argv[0]+"?mode=settings"
  listfolder = xbmcgui.ListItem(language(30101)) #asetukset
  listfolder.setInfo('video', {'Title': language(30101)})
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)



  t2.replace(hour=0, minute=0, second=0, microsecond=0)
  for d in range(0,20):
    ta=t2-datetime.timedelta(days=d+1)
    tb=t2-datetime.timedelta(days=d)
    data = json.dumps({"from":ta.isoformat(),"to":tb.isoformat()})  
    u=sys.argv[0]+"?mode=listprograms&url=epg/range&data="+requests.utils.quote(data)
    title=ta.strftime("%A %-d %b")
    listfolder = xbmcgui.ListItem(title)
    listfolder.setInfo('video', {'Title': title})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  xbmcplugin.endOfDirectory(int(sys.argv[1]))

def speedtest():
  #get a list of servers and do a speedtest. Store the resulting prioritized list of hosts in a setting.
  global PLAYROOT
  dp = xbmcgui.DialogProgress() 
  dp.create('Running speedtests')
  servers=apiget('cache/get','')
  for ix,server in enumerate(servers):
    dp.update(ix*100/len(servers),server['country'],server['host'])
    if server['status']=='up':
      url = 'http://%s/speedtest_1mb.bin' % (server['host'])
      start=time.time()
      requests.get(url)
      delta=time.time()-start
      server['speed']=8.0/delta
    else:
      server['speed']=0.0
    if dp.iscanceled(): #TODO: it will fail below if not all servers have a speed....
      break
  dp.close()
  servers=sorted(servers, key=lambda k: -k['speed'])
  xbmc.log('telkkarista speedtest result:'+repr(servers))
  hosts=[k['host'] for k in servers]
  telkkarista_addon.setSetting("preferredhosts",",".join(hosts))
  PLAYROOT=hosts[0]
  telkkarista_addon.setSetting("currentcachehost",PLAYROOT) #Found preferredhost
  
def parsedate(datestr):
  t=dateutil.parser.parse(datestr)
  t=t.astimezone(dateutil.tz.tzlocal())
  return t
  

#list the programs in a feed
def listprograms(url,data):
  #try:
  content=apiget(url,data)
  sessionkey=telkkarista_addon.getSetting("sessionkey")
  #except:
  #  desc=''
  #  u=sys.argv[0]
  #  listfolder = xbmcgui.ListItem(language(30203)+' '+desc) #www-pyyntö ei onnistunut
  #  listfolder.setInfo('video', {'Title': language(30203)+' '+desc})
  #  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=0)
  #  xbmcplugin.endOfDirectory(int(sys.argv[1]))
  #  return
  assumeRecordInStorage=False
  if type(content) is list: #epg/search gives a list, epg/range gives a dict of lists with one item per channel. 
    content={'all': content}
    assumeRecordInStorage=True #epg/search does not return a record field
  for stream in content:
    channel=stream
    for p in content[stream]:
      if not ('record' in p):
        if assumeRecordInStorage: 
          p['record']='storage'
        else: 
          continue #skip if it is not recorded yet
      if p['record']=='pending': continue
      if 'channel' in p: channel=p['channel']
      title=p['title']['fi']
      pid=p['pid']
      start=parsedate(p['start'])
      stop=parsedate(p['stop'])
      subtitle='%s  %imin\n%s' % (channel.upper(), (stop-start).seconds/60, repr(p))
      if not p['record']=='storage': title='%s [%s]' % (title,p['record'])
      #epgi=apiget('epg/info',{'pid':pid}) #slows it down for long lists....
      #try:
      #  subtitle=epgi['sub-title']['fi']
      #except Exception, e:
      #  pass
      label = '%s | %s' % (start.strftime('%H:%M'),title)
      listitem = xbmcgui.ListItem(label=label, iconImage="DefaultVideo.png")
      listitem.setProperty('IsPlayable','true')
      infoLabels={'Title': label, 
                  'ChannelName': channel,
                  'PlotOutline': subtitle,
                  'Plot': subtitle,
                  'Genre': channel,
                  'Date': start.strftime("%d.%m.%Y"),
                  'Duration': (stop-start).seconds/60}
      listitem.setInfo(type='Video', infoLabels=infoLabels)
      try:
        #playurl = 'http://%s/%s/vod%smaster.m3u8' % (PLAYROOT, sessionkey, epgi['recordpath'])
        #xbmc.log(playurl)
        #pt=start.strftime('%Y/%m/%d')
        #playurl = 'http://%s/%s/vod/%s/%s/%s/master.m3u8' % (PLAYROOT, sessionkey, pt, pid,channel)
        data = json.dumps({"pid":pid});
        u=sys.argv[0]+"?mode=playitem&data="+requests.utils.quote(data)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=listitem)
        #break
      except:
        pass
  xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
 # xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

def livetv():
  xbmc.log('telkkarista livetv')
  t=datetime.datetime.now()
  content=apiget('streams/get','')
  current=apiget('epg/current','')
  sessionkey=telkkarista_addon.getSetting("sessionkey")

  content=sorted(content, key=lambda k: k['streamOrder']) 
  for p in content:
    channel=p['name']
    title=p['visibleName']
    try:
      c=current[channel][0]
      subtitle=c['title']['fi']
    except Exception, e:
      subtitle=''   
    playurl = 'http://%s/%s/live/%s.m3u8' % (PLAYROOT, sessionkey, channel)
    iconurl='http://%s/%s/live/%s_small.jpg?%i' % (PLAYROOT, sessionkey, channel, random.randint(0,2e9))
    listitem = xbmcgui.ListItem(label=title, iconImage=iconurl)
    infoLabels={'Title': title,
                'ChannelName': channel,
                'PlotOutline': subtitle,
                'Plot': subtitle}
    listitem.setInfo(type='Video', infoLabels=infoLabels)
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=playurl,listitem=listitem)
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

def playitem(data):
  #data=json.loads(data)
  #pid=data['pid']
  epgi=apiget('epg/info',data)
  quality=telkkarista_addon.getSetting("quality").split()
  sessionkey=telkkarista_addon.getSetting("sessionkey")

  #fallback:
  playurl = 'http://%s/%s/vod%smaster.m3u8' % (PLAYROOT, sessionkey, epgi['recordpath'])
  try:
    if quality[1]=='mp4':
      if quality[0] in epgi['downloadFormats']['mp4']:
        mp4quality=quality[0]   
      else:  
        mp4quality=epgi['downloadFormats']['mp4'][0] #assume first =highest quality
      playurl = 'http://%s/%s/vod%s%s.mp4' % (PLAYROOT, sessionkey, epgi['recordpath'],mp4quality)
  except:  
    pass
  xbmc.log('Telkkarista RESOLVED PLAY URL=%s' % (playurl))
  try:
    subtitle = epgi['sub-title']['fi']
  except:
    subtitle=''
  listitem = xbmcgui.ListItem(label=epgi['title']['fi'], iconImage="DefaultVideo.png", path=playurl)
  infoLabels={'Title': epgi['title']['fi'], 
              'ChannelName': epgi['channel'],
              'PlotOutline': subtitle,
              'Plot': subtitle}
  #xbmc.Player().play(playurl,listitem)
  xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listitem)
  #xbmc.Player().play(playurl,listitem)

# display the virtual keyboard and lists search results
def search():
  keyboard = xbmc.Keyboard()
  keyboard.doModal()
  if (keyboard.isConfirmed() and keyboard.getText() != ''):
    list=telkkarista_addon.getSetting("searches").splitlines()
    try:
      list.remove(keyboard.getText())
    except ValueError:
      pass
    if len(list)>20: list.pop()
    list.insert(0,keyboard.getText())
    telkkarista_addon.setSetting("searches","\n".join(list))
    data = {"search":keyboard.getText()};
    listprograms('epg/search',data)

#list searches that are stored in plugin settings
def listsearches():
  u=sys.argv[0]+"?mode=search"
  listfolder = xbmcgui.ListItem(language(30118)) #'Uusi haku'
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  for i in telkkarista_addon.getSetting("searches").splitlines():
    data = json.dumps({"search":i});
    u=sys.argv[0]+"?mode=listprograms&url=epg/search&data="+requests.utils.quote(data)
    listfolder = xbmcgui.ListItem(language(30106)+': '+i.decode('utf-8')) #haku
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

  if(telkkarista_addon.getSetting("searches") != ""):
    u=sys.argv[0]+"?mode=delsearches"
    listfolder = xbmcgui.ListItem(language(30119)) #'Poista viimeiset haut'
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
  xbmcplugin.endOfDirectory(int(sys.argv[1]))


#delete stored searches
def delsearches():
  dialog = xbmcgui.Dialog()
  if(dialog.yesno('telkkarista', language(30120))): #'Poistetaanko viimeiset haut?'
    telkkarista_addon.setSetting("searches","")
    dialog.ok('telkkarista', language(30121)) #'Viimeiset haut poistettu.'


xbmc.log('TELKKARISTA\n'+repr(sys.argv))

params=dict(urlparse.parse_qsl(urlparse.urlparse(sys.argv[2]).query))#urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)
mode=None
data=None
url=None
try:
  mode=params["mode"]
  data=params["data"]
  url=params["url"]
except:
  pass

xbmc.log('TELKKARISTA\n'+repr(params))


if mode==None:
  settings()
elif mode=='playitem':
  playitem(data)
elif mode=='listprograms':
  listprograms(url,data)
elif mode=='search':
  search()
elif mode=='settings':
  telkkarista_addon.openSettings(url=sys.argv[0])
elif mode=='live':
  livetv()
elif mode=='listsearches':
  listsearches()
elif mode=='delsearches':
  delsearches()
elif mode=='speedtest':
  speedtest()
else:
  xbmc.log('TELKKARISTA UNKNOWN MODE')