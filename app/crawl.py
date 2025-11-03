from bs4 import BeautifulSoup
import json
import os
import re
import requests

def get_main_info(soup: BeautifulSoup):
	header = soup.find('h1')
	if header is None:
		raise ValueError('Could not find <h1> in the HTML')

	main_info = header.text.strip()

	# find double colon between degree+name and thesis title
	separator_idx = main_info.find(':')
	if separator_idx == -1:
		raise ValueError("Could not find ':' separator between degree+name and title")

	degree_name = main_info[:separator_idx].strip()
	title = main_info[separator_idx + 1:].replace('- Einzelansicht', '').strip()

	# find first name abbreviation (e.g., "A." in "Max A. Mustermann")
	pattern = r'\s[A-Z]\.'
	match = re.search(pattern, degree_name)
	if not match:
		raise ValueError('Could not parse student name abbreviation in degree+name')

	separator_idx = match.start()
	degree = degree_name[:separator_idx].strip()
	student = degree_name[separator_idx:].strip()
	return dict(degree=degree, student=student, title=title)


def parse_examiners(soup:BeautifulSoup):
	table = soup.find('table', {'summary': 'Verantwortliche Dozenten'})
	if table is None:
		raise ValueError('Could not find <table summary="Verantwortliche Dozenten"> in the HTML')

	examiners = table.select('a.regular')
	return [e.text.strip() for e in examiners]


def parse_appointment(soup: BeautifulSoup):
	data = dict(date='-', start='-', end='-', location='-')

	table = soup.find('table', {'summary': 'Übersicht über alle Veranstaltungstermine'})
	if table is None:
		return data 

	rows = table.find_all('tr')
	if len(rows) < 2:
		return data  # no data row available

	cells = rows[1].find_all('td')

	# safely extract start/end times
	if len(cells) > 2:
		times = re.findall(r'\d+:\d+', cells[2].text)
		if len(times) >= 1:
			data['start'] = times[0]
		if len(times) >= 2:
			data['end'] = times[1]

	# safely extract date
	if len(cells) > 4:
		date_match = re.search(r'\d+\.\d+\.\d+', cells[4].text)
		if date_match:
			data['date'] = date_match.group(0)

	# safely extract date
	if len(cells) > 5:
		data['location'] = cells[5].text.strip()

	# safely extract note
	if len(cells) > 8:
		note = cells[8].text.strip()
		if note:
			data['note'] = note
	return data


def get_defense_data(soup:BeautifulSoup):
	data = get_main_info(soup)
	data.update(parse_appointment(soup))
	data['examiners'] = parse_examiners(soup)
	return data


def get_soup(url):
	id_match = re.search(r'publishid=(\d+)', url)
	if id_match:
		id = id_match.group(1)
		filepath = f'./pages/{id}.html'

	if id_match:
		id = id_match.group(1)
		if os.path.isfile(filepath):
			with open(filepath, 'r', encoding='utf-8') as f:
				text = f.read()
			text = re.sub(r'&nbsp;', ' ', text) #idk whatever
			return BeautifulSoup(text, 'html.parser')

	if id_match:
		print(f'query {id}...')
	response = requests.get(url)
	response.raise_for_status()
	text = response.text

	if id_match:
		with open(filepath, 'w', encoding='utf-8') as f:
			f.write(text)
	text = re.sub(r'&nbsp;', ' ', text) #could also unicodedata.normalize after bs4 parsing
	return BeautifulSoup(text, 'html.parser')


def get_saved_soup(filename):
	with open(filename, 'r', encoding='utf-8') as f:
		text = f.read()
	text = re.sub(r'&nbsp;', ' ', text) #idk whatever
	return BeautifulSoup(text, 'html.parser')


def get_defense_urls(soup:BeautifulSoup):
	table = soup.find('table', {'summary': 'Übersicht über alle Veranstaltungen'})
	defense_entries = table.select('a.regular', href=True)
	return [a['href'] for a in defense_entries]


def get_all_defenses(overview_soup:BeautifulSoup):
	defense_urls = get_defense_urls(overview_soup)
	defenses = {}

	for url in defense_urls:
		defense_soup = get_soup(url)
		id = re.search(r'publishid=(\d+)', url).group(1) 
		try:
			data = get_defense_data(defense_soup)
			data['url'] = url
			defenses[id]= data
		except Exception as e:
			print(f'error parsing {id}:', e)
	return defenses


def load_last_crawl(filepath):
	if os.path.isfile(filepath):
		with open(filepath, 'r', encoding='utf-8') as f:
			return json.load(f)
	return []


def save_crawl(defenses, filepath):
	with open(filepath, 'w', encoding='utf-8') as f:
		json.dump(defenses, f, indent=4)


def get_new_defense_items(old_crawl, new_crawl):
	return {k: v for k, v in new_crawl.items() if k not in old_crawl}


def test_save(url, filename, prettify=False):
	response = requests.get(url)
	response.raise_for_status()
	html = response.text
	if prettify:
		soup = BeautifulSoup(html, 'html.parser')
		html = soup.prettify()
		filename += '_pretty'
	
	with open(filename, 'w', encoding='utf-8') as f:
		f.write(html)
	

def main():
	bison_overview_url = 'https://bison.uni-weimar.de/qisserver/rds?state=wtree&search=1&P.vx=kurz&root120252=44747%7C44160%7C43798%7C44232%7C44238&trex=step'
	json_filepath = 'defenses.json'
	os.makedirs('./pages', exist_ok=True)

	overview_soup = get_soup(bison_overview_url)
	new_crawl = get_all_defenses(overview_soup)
	# old_crawl = load_last_crawl(json_filepath)
	# new_items = get_new_defense_items(old_crawl, new_crawl)
	# print('these defenses new', list(new_items.keys()))
	save_crawl(new_crawl, json_filepath)
	print("Posts fetched. Total:", len(new_crawl))

if __name__ == '__main__':
	bison_overview_url = 'https://bison.uni-weimar.de/qisserver/rds?state=wtree&search=1&P.vx=kurz&root120252=44747%7C44160%7C43798%7C44232%7C44238&trex=step'
	# test_save(bison_overview_url, 'overview.html', True)
	main()
