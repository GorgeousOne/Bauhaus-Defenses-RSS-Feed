from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from jinja2 import Template
import json
from fastapi import FastAPI, Response
from feedgen.feed import FeedGenerator
import logging
import markdown

import crawl


LOG = logging.getLogger('rss_app')
logging.basicConfig(level=logging.INFO)

app = FastAPI()
posts_cache = []
template_path = './post_template.md'

def load_posts():
	global posts_cache
	with open(template_path, 'r') as f:
		template = f.read()
	with open('./defenses.json') as f:
		defenses = json.load(f)
	asc_defenses = sorted(list(defenses.values()), key=lambda d: datetime.strptime(d['date'], "%d.%m.%Y"), reverse=True)
	posts_cache = [render_template(template, d) for d in asc_defenses]
	print('Posts reloaded. Total:', len(posts_cache))


def fetch_defenses():
	crawl.main()
	load_posts()


def render_template(template_str, defense):
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
	fetch_defenses() 
	scheduler = BackgroundScheduler()
	scheduler.add_job(load_posts, 'interval', hours=6, id='reload_posts_job', replace_existing=True)
	scheduler.start()

	app.state.scheduler = scheduler
	LOG.info('Scheduler started (reload every 6 hours).')


@app.get('/rss.xml')
def rss_feed():
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


from fastapi.responses import HTMLResponse

@app.get("/")
def preview():
    html = "<h1>Feed Preview</h1>"
    for post in posts_cache:
        html += f"<h2><a href='{post['url']}'>{post['title']}</a></h2>{post['content']}"
    return HTMLResponse(content=html)