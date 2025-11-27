from datetime import datetime
from jinja2 import Template
import json
import logging
import markdown

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse
from feedgen.feed import FeedGenerator

import crawl


LOG = logging.getLogger('rss_app')
logging.basicConfig(level=logging.INFO)

app = FastAPI()
posts_cache = []
template_path = './post_template.md'

def load_posts():
	'''load the posts of the crawled defenses.json to cache'''
	global posts_cache
	with open(template_path, 'r') as f:
		template = f.read()
	with open('./defenses.json') as f:
		defenses = json.load(f)

	asc_defenses = sorted(list(defenses.values()), key=lambda d: datetime.strptime(d['date'], "%d.%m.%Y"), reverse=True)
	today = datetime.today()
	new_defenses = [d for d in asc_defenses if datetime.strptime(d['date'], "%d.%m.%Y") >= today]
	posts_cache = [render_template(template, d) for d in new_defenses]
	LOG.info(f'Posts reloaded. Total: {len(posts_cache)}')


def fetch_defenses():
	'''trigger crawling bison & loading posts'''
	# crawl.main(LOG)
	load_posts()


def render_template(template_str, defense):
	'''turn defense data to rss format dict'''
	template = Template(template_str)
	rendered_md = template.render(**defense)

	title = f"{defense['date']}: {defense['degree']} - {defense['student']}"
	content_html = markdown.markdown(rendered_md)

	return {
		'title': title,
		'url': defense.get('url', '#'),
		'content': content_html
	}


@app.on_event('startup')
def startup_event():
	'''crawl once on startup, then cron schedule every 6 hours'''
	fetch_defenses()
	scheduler = BackgroundScheduler()
	scheduler.add_job(
		fetch_defenses,
		trigger='cron',
		hour='0,6,12,18',
		minute=0,
		id='reload_posts_job',
		replace_existing=True
	)
	scheduler.start()

	app.state.scheduler = scheduler
	LOG.info('Scheduler started (reload every 6 hours).')


@app.get('/rss.xml')
def rss_feed():
	'''serve cached rss'''
	fg = FeedGenerator()
	fg.title('Medieninformatik Verteidigungen')
	fg.link(href='https://bison.uni-weimar.de/qisserver/rds?state=wtree&search=1&trex=step&root120252=44747%7C44160%7C43798%7C44232%7C44238&P.vx=kurz', rel='alternate')
	fg.description('Aktuelle Informationen über Bachelor- und Masterverteidigungen im Fachbrereich Informatik')

	for post in posts_cache:

		fe = fg.add_entry()
		fe.title(post['title'])
		fe.link(href=post['url'])
		fe.description(post['content'])

	rss_bytes = fg.rss_str(pretty=True)
	return Response(content=rss_bytes, media_type='application/rss+xml')


@app.get("/")
def preview():
	'''serve html preview of cached rss feed'''
	html = "<h1>Feed Preview</h1>"
	for post in posts_cache:
		html += f"<h2><a href='{post['url']}'>{post['title']}</a></h2>{post['content']}"
	return HTMLResponse(content=html)