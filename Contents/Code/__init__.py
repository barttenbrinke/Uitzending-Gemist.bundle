TITLE = 'Uitzending Gemist'
BASE_URL = 'http://www.uitzendinggemist.nl'
EPISODE_URL = '%s/afleveringen/%%s#%%s;%%s' % BASE_URL

####################################################################################################
def Start():

	Plugin.AddViewGroup('List', viewMode='List', mediaType='items')
	Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')

	ObjectContainer.title1 = TITLE
	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_4) AppleWebKit/536.30.1 (KHTML, like Gecko) Version/6.0.5 Safari/536.30.1'
	HTTP.Headers['Cookie'] = 'npo_cc=30'

####################################################################################################
@handler('/video/uzg', TITLE)
def MainMenu():

	oc = ObjectContainer()

	oc.add(DirectoryObject(key=Callback(Recent, title='Afgelopen 7 dagen'), title='Afgelopen 7 dagen'))
#	oc.add(DirectoryObject(key=Callback(Broadcaster, title='Programma\'s per Omroep'), title='Programma\'s per Omroep'))
#	oc.add(DirectoryObject(key=Callback(Genre, title='Programma\'s per Genre'), title='Programma\'s per Genre'))
#	oc.add(DirectoryObject(key=Callback(AtoZ, title='Programma\'s A-Z'), title='Programma\'s A-Z'))

	# Do not show search on Rokus. Search finds mostly older videos which are all in M4V format (not HLS) and Roku playback always fails.
	if Client.Platform not in ('Roku'):
		oc.add(SearchDirectoryObject(identifier='com.plexapp.plugins.uzgv2', title='Zoeken', prompt='Zoek uitzendingen', term='Uitzendingen'))

	return oc

####################################################################################################
@route('/video/uzg/recent')
def Recent(title):

	oc = ObjectContainer(title2=title, view_group='List', no_cache=True)

	for day in HTML.ElementFromURL(BASE_URL).xpath('//ol[@id="daystoggle"]/li/a')[:7]:
		title = day.text.replace('  ', ' ').strip()
		url = '%s%s?_pjax=true' % (BASE_URL, day.get('href'))

		oc.add(DirectoryObject(
			key = Callback(BrowseByDay, title=title, url=url),
			title = title
		))

	return oc

####################################################################################################
@route('/video/uzg/browse/day', page=int)
def BrowseByDay(title, url, page=1):

	ids = []
	url = '%s&page=%d' % (url, page)

	try:
		html = HTML.ElementFromURL(url)
	except:
		return ObjectContainer(header="Error", message="Er ging iets fout bij het ophalen van data")

	for episode_url in html.xpath('//a[contains(@href, "/afleveringen/") and @title=""]/@href'):
		episode_id = episode_url.split('/')[-1]

		if episode_id.isdigit() and episode_id not in ids:
			ids.append(episode_id)

	oc = Episodes(title, ids)

	if len(oc) < 1:
		return ObjectContainer(header="Geen programma's", message="Er staan voor deze dag nog geen programma's op Uitzending Gemist")

	next_page = html.xpath('//a[text()="Volgende"]')

	if len(next_page) > 0:
		oc.add(NextPageObject(
			key = Callback(BrowseByDay, title=title, url=url, page=page+1),
			title = 'Meer...'
		))

	return oc

####################################################################################################
def Episodes(title, ids):

	oc = ObjectContainer(title2=title, view_group='InfoList', no_cache=True)
	result = {}
	client_platform = Client.Platform if Client.Platform is not None else ''
	client_version = Client.Version if Client.Version is not None else ''

	@parallelize
	def GetEpisodes():

		for id in ids:
			result[id] = None

			@task
			def GetEpisode(result=result, id=id):

				try:
					result[id] = URLService.MetadataObjectForURL(EPISODE_URL % (id, client_platform, client_version))
				except:
					pass

	for id in ids:
		if result[id] is not None:
			oc.add(result[id])

	return oc
