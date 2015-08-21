# -*- coding: utf-8 -*-
TITLE  = u'Short of the Week'
PREFIX = '/video/shortoftheweek'

SOTW_ICON = 'sotw.png'
ICON      = 'default.png'
ART       = 'background.jpg'

SOTW_BASE_URL   = 'https://www.shortoftheweek.com'
SOTW_HOME_URL   = '%s/' % SOTW_BASE_URL
SOTW_CHANNELS   = '%s/channels/' % SOTW_BASE_URL
SOTW_SEARCH_URL = '%s/search/?q={0}' % SOTW_BASE_URL

RE_POSTS = Regex('json_posts:\s({.+?})\s+}\);')

HTTP_HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:29.0) Gecko/20100101 Firefox/29.0',
  'Accept-Encoding': 'gzip, deflate',
  'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
  'Connection': 'keep-alive',
  'Referer': SOTW_BASE_URL
}

################################################################################
def Start():

  Plugin.AddViewGroup('List', viewMode='List', mediaType='items')
  Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')
  Plugin.AddViewGroup('PanelStream', viewMode='PanelStream', mediaType='items')

  ObjectContainer.title1 = TITLE
  #ObjectContainer.view_group = 'List'
  ObjectContainer.art = R(ART)
  DirectoryObject.thumb = R(ICON)
  DirectoryObject.art = R(ART)

  HTTP.CacheTime = CACHE_1HOUR

################################################################################
@handler(PREFIX, TITLE, art=ART, thumb=SOTW_ICON)
def sotw_main_menu():

  oc = ObjectContainer()

  oc.add(DirectoryObject(
    key = Callback(
      sotw_get_shorts,
      url = SOTW_HOME_URL,
      title = L('Shorts of the Week')
    ),
    title = L('Shorts of the Week'),
    summary = L('most recent shorts of the week')
  ))

  oc.add(DirectoryObject(
    key = Callback(
      sotw_get_sections,
      title = L('Genders'),
      position = 0
    ),
    title = L('Genders'),
    summary = L('select a short by gender')
  ))

  oc.add(DirectoryObject(
    key = Callback(
      sotw_get_sections,
      title = L('Topics'),
      position = 1
    ),
    title = L('Topics'),
    summary = L('select a short by topic')
  ))

  oc.add(DirectoryObject(
    key = Callback(
      sotw_get_sections,
      title = L('Styles'),
      position = 2
    ),
    title = L('Styles'),
    summary = L('select a short by style')
  ))

  oc.add(DirectoryObject(
    key = Callback(
      sotw_get_sections,
      title = L('Collections'),
      position = 3
    ),
    title = L('Collections'),
    summary = L('review the collections of shorts')
  ))

  oc.add(DirectoryObject(
    key = Callback(
      sotw_get_sections,
      title = L('Countries'),
      position = 4
    ),
    title = L('Countries'),
    summary = L('select a short by country')
  ))

  if Client.Product != 'PlexConnect':
    oc.add(InputDirectoryObject(
      key     = Callback(sotw_search),
      title   = L('Search Shorts'),
      prompt  = L('Search for Shorts'),
      summary = L('Search for Shorts')
    ))

  return oc

################################################################################
@route(PREFIX+'/sections', position = int)
def sotw_get_sections(title, position = 0):

  oc = ObjectContainer(
    title2 = title
  )

  data = HTML.ElementFromURL(
    SOTW_CHANNELS,
    headers = HTTP_HEADERS,
    cacheTime = CACHE_1HOUR
  )

  for section in data.xpath('//div[contains(@class, "category-list")]')[position]:
    section_url = section.xpath('.//@href')[0]
    section_title = section.xpath('.//h3/text()')[0].strip()
    oc.add(DirectoryObject(
      key = Callback(
        sotw_get_shorts,
        url = section_url,
        title = section_title
      ),
      title = section_title
    ))
	
  return oc

################################################################################
@route(PREFIX+'/shorts', page = int)
def sotw_get_shorts(url, title, page = 1):

  requrl = url + '?page={0}'
  requrl = requrl.format(page)

  html = HTTP.Request(
    requrl,
    headers = HTTP_HEADERS,
    cacheTime = CACHE_1HOUR
  ).content

  data = JSON.ObjectFromString(
    RE_POSTS.search(html).group(1)
  )

  oc = ObjectContainer(
    title2 = title + ' | ' + L('Page') + ' ' + str(page)
  )

  for short in data['data']:
    try:
      if short['play_link'] and URLService.ServiceIdentifierForURL(short['play_link']):
        oc.add(VideoClipObject(
          url = short['play_link'],
          title = short['post_title'],
          summary = short['post_excerpt'],
          thumb = Resource.ContentsOfURLWithFallback('https:' + short['background_image'])
        ))
    except:
      pass

  if data['page'] < data['page_max']:
    oc.add(NextPageObject(
      key = Callback(
        sotw_get_shorts,
        url = url,
        title = title,
        page = page + 1
      ),
      title = L('Next Page') + ' >>'
    ))

  return oc

################################################################################
@route(PREFIX+'/search')
def sotw_search(query):

  noresults = ObjectContainer(
    header   = L('Short not found'),
    message  = L('Short not found'),
    no_cache = True
  )

  oc = ObjectContainer(
    title2 = unicode(L('Search Results') + ': ' + query )
  )

  html = HTTP.Request(
    SOTW_SEARCH_URL.format(String.Quote(query, usePlus=True)),
    headers = HTTP_HEADERS,
    cacheTime = CACHE_1HOUR
  ).content

  data = JSON.ObjectFromString(
    RE_POSTS.search(html).group(1)
  )

  if data['count'] == 0:
    return noresults

  for short in data['data']:
    if short['type'] == 'video' and ('vimeo' in short['play_link'] or 'youtube' in short['play_link']):
      oc.add(VideoClipObject(
        url = short['play_link'],
        title = short['post_title'],
        summary = short['post_excerpt'],
        thumb = Resource.ContentsOfURLWithFallback('https:' + short['background_image'])
      ))

  return oc
