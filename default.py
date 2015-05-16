#kodi telkkarista plugin
# This Python file uses the following encoding: utf-8
#
# This plugin is modelled over the now defunct TVKaista plugin. 
# Ackownledgements goes to Viljo Viitanen,sampov2,stilester,& J. Luukko
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
import dateutil.parser
telkkarista_addon = xbmcaddon.Addon("plugin.video.telkkarista");
language = telkkarista_addon.getLocalizedString


BASE_RESOURCE_PATH = xbmc.translatePath( os.path.join( telkkarista_addon.getAddonInfo('path'), "resources" ) )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

from string import split, replace, find

APIROOT='http://api.telkkarista.com/1/'
#PLAYROOT='http://46.166.187.206' #todo list servers and autopick....
PLAYROOT='http://proxy1.telkkarista.com'

def login():
  headers = {'User-Agent': "telkkarista for kodi version "+VERSION+";"}
  data={'email': telkkarista_addon.getSetting("username"), 'password': telkkarista_addon.getSetting("password")}
  response=requests.post(url=APIROOT+'user/login',data=json.dumps(data),headers=headers)
  #TODO add checks for server down and expired key....
  response=response.json()
  sessionkey=response['payload']
  xbmc.log('TELKKARISTA LOGIN!')
  telkkarista_addon.setSetting("sessionkey",sessionkey)

def apiget(url,data,allowrecursion=True):
  sessionkey=telkkarista_addon.getSetting("sessionkey")
  if sessionkey=='': login()
  headers = {'X-SESSION': sessionkey, 'User-Agent': "telkkarista for kodi version "+VERSION+";"}
  if not isinstance(data, basestring):
    data = json.dumps(data)
  response=requests.post(url=APIROOT+url,data=data,headers=headers)
  #TODO add checks for server down ....
  response=response.json()
  #if key expired:
  if response['status'] == 'error':
    if response['code'] == 'invalid_session':
      if allowrecursion:
        abmx.log('Telkkarista invalid session - logging in...')
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
  data = json.dumps({"from":t1.isoformat(),"to":t2.isoformat()})
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





#list the programs in a feed
def listprograms(url,data):
  #print "listprograms avataan: "+url+'/'+bitrate()+'.rss'
  xbmc.log('telkkarista listprograms'+url+data)
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
  if type(content) is list: 
    content={'all': content}
    assumeRecordInStorage=True
  for stream in content:
    channel=stream
    for p in content[stream]:
      xbmc.log(repr(p))
      if not ('record' in p):
        if assumeRecordInStorage: 
          p['record']='storage'
        else: 
          continue #skip if it is not recorded yet
      if p['record']=='pending': continue
      if 'channel' in p: channel=p['channel']
      title=p['title']['fi']
      pid=p['pid']
      start=dateutil.parser.parse(p['start'])
      stop=dateutil.parser.parse(p['stop'])
      subtitle='%s  %imin\n%s' % (channel.upper(), (stop-start).seconds/60, repr(p))
      if not p['record']=='storage': title='%s [%s]' % (title,p['record'])
      #epgi=apiget('epg/info',{'pid':pid}) #slows it down for long lists....
      #try:
      #  subtitle=epgi['sub-title']['fi']
      #except Exception, e:
      #  pass
      label = '%s | %s' % (start.strftime('%H:%M'),title)
      listitem = xbmcgui.ListItem(label=label, iconImage="DefaultVideo.png")
      infoLabels={'Title': label, 
                  'ChannelName': channel,
                  'PlotOutline': subtitle,
                  'Plot': subtitle,
                  'Genre': channel,
                  'Date': start.strftime("%d.%m.%Y"),
                  'Duration': (stop-start).seconds/60}
      listitem.setInfo(type='Video', infoLabels=infoLabels)
      try:
        #playurl = '%s/%s/vod%smaster.m3u8' % (PLAYROOT, sessionkey, epgi['recordpath'])
        #xbmc.log(playurl)
        pt=start.strftime('%Y/%m/%d')
        playurl = '%s/%s/vod/%s/%s/%s/master.m3u8' % (PLAYROOT, sessionkey, pt, pid,channel)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=playurl,listitem=listitem)
        #break
      except:
        pass
  xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
  xbmcplugin.endOfDirectory(int(sys.argv[1]))


def livetv():
  xbmc.log('telkkarista livetv')
  t=datetime.datetime.now()
  content=apiget('streams/get','')
  sessionkey=telkkarista_addon.getSetting("sessionkey")
  content=sorted(content, key=lambda k: k['streamOrder']) 
  for p in content:
    channel=p['name']
    title=p['visibleName']
    playurl = '%s/%s/live/%s.m3u8' % (PLAYROOT, sessionkey, channel)
    #http://46.166.187.206/55568915febb6c574beb42fb.-43b36895/live/yletv1.m3u8
    iconurl='%s/%s/live/%s_small.jpg?%i' % (PLAYROOT, sessionkey, channel, random.randint(0,2e9))
    #http://46.166.187.206/55568915febb6c574beb42fb.-43b36895/live/nelonen_small.jpg?1431734568978
    listitem = xbmcgui.ListItem(label=title, iconImage=iconurl)
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=playurl,listitem=listitem)
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

# displays the virtual keyboard and lists search results
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
  xbmc.log('telkkarista search')
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


#main program


#params=get_params()
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
#elif mode=='listfeeds':
#  listfeeds(url)
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
else:
  xbmc.log('TELKKARISTA UNKNOWN MODE')