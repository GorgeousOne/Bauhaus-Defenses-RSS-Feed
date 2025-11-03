from fastapi import FastAPI, Response
from feedgen.feed import FeedGenerator
import json

app = FastAPI()
posts_cache = []

def load_posts():
	global posts_cache
	with open("app/defenses.json") as f:
		defenses = json.load(f)
		posts_cache = [create_defense_post(d) for d in defenses]
	print("Posts reloaded. Total:", len(posts_cache))


def create_defense_post(defense):
	return {
		'title': defense['title'],
		'url': defense['url'],
		'content': 
	}

@app.on_event("startup")
def startup_event():
	load_posts() 

	scheduler = BackgroundScheduler()
	scheduler.add_job(load_posts, 'interval', hours=6)
	scheduler.start()


@app.get('/rss.xml')
def rss_feed():
	fg = FeedGenerator()
	fg.title('Medieninformatik Verteidigungen')
	fg.link(href='https://bison.uni-weimar.de/qisserver/rds?state=wtree&search=1&trex=step&root120252=44747%7C44160%7C43798%7C44232%7C44238&P.vx=kurz', rel='alternate')
	fg.description('Aktuelle Informationen über Bachelor- und Masterverteidigungen im Fachbrereich Informatik')

	with open('app/posts.json') as f:
		posts = json.load(f)

	for post in posts_cache:
		fe = fg.add_entry()
		fe.title(post["title"])
		fe.link(href=post["url"])
		fe.description(post["content"])

	return Response(content=fg.rss_str(pretty=True), media_type="application/rss+xml")
