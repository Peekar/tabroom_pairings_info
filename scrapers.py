from bs4 import BeautifulSoup
from selenium import webdriver
import requests

# TODO:
#   - make a JSON file to save all of the information related to a tournament so it won't be necessary to scrape
#     all the sites again
#       - only scrape the first time around, OR run a script that pre-scrapes before the tournament
#       - just go to pairings, find the opponents and judge, then go to the JSON and get the links
#   - make a get_pairings() function, a more efficient version of html_table_to_dict()'s stop feature
#   - make a function to make add "Full Name" to the judge dictionary (code is in get_judge_paradigm(), but need it to
#     to be separate for the JSON file


# some functions to make the code more readable
def clean_html(html_text):
    return html_text.strip().replace('\n', ' ').replace('\t', '')

def link_split(link, split):
    return link.split(split)[1]


# converts a html table (from a link) to a python dictionary
# different parameters are for the different types of tables on the Tabroom.com site
def html_table_to_dict_list(page_link, stop=None, pairings=False, hrefed=False, headless_webdriver=False):

    # the pages that have links in tables
    HREFED = ['Record', 'Paradigm', 'Tournament Name']

    # requests only gets the initial site, before any JS loading
    # selenium webdriver gets it after by using a headless Chrome browser
    if headless_webdriver:
        headless = webdriver.ChromeOptions()
        headless.add_argument('--headless')
        driver = webdriver.Chrome(options=headless)
        driver.get(page_link)
        page_html = driver.page_source
        driver.quit()
    else:
        page_html = requests.get(page_link).text
    soup = BeautifulSoup(page_html, 'html.parser').find('table')

    # TODO: base_dict isn't needed since the only the order of the header needs to be saved, so instead save everything
    #   in order to the dict_order list
    base_dict = {}
    empty_counter = 0
    for th in soup.find('thead').find_all('th'):
        th_text = clean_html(th.get_text())

        if th_text == '':

            if pairings:
                if empty_counter == 0:
                    base_dict['Team 1'] = None
                    empty_counter += 1
                base_dict['Team 2'] = None
                continue

            empty_counter += 1
            base_dict[f'Blank ${empty_counter}'] = None

        base_dict[th_text] = None

    dict_order = []
    for key in base_dict.keys():
        dict_order.append(key)

    table_list = []

    for tr in soup.find_all('tr')[1:]:
        append_dict = base_dict.copy()

        key_counter = 0
        for td in tr.find_all('td'):
            # normally a link embedded in the table will come as an empty string (as the link is in the HTML tag),
            # making it so that it is instead the link itself in the dictionary
            if hrefed and (dict_order[key_counter] in HREFED):
                a = td.find('a')
                if a is not None:
                    href = a.get('href')
                    if dict_order[key_counter] == 'Tournament Name':
                        append_dict['Tournament Name'] = clean_html(td.get_text())
                        append_dict['Tournament Link'] = "https://www.tabroom.com/" + href
                    else:
                        append_dict[dict_order[key_counter]] = "https://www.tabroom.com/" + href
                    key_counter += 1
                    continue

            append_dict[dict_order[key_counter]] = clean_html(td.get_text())
            key_counter += 1

        for value in append_dict.values():
            # likely will remove stop after the JSON info file is created, as we want to load all the data the first
            # time around
            if value == stop:
                return [append_dict]

        table_list.append(append_dict)

    return table_list


def get_tourn_id(tourn_name):
    url = f"https://www.tabroom.com/index/search.mhtml?search=${tourn_name}&caller=%2Findex%2Findex.mhtml"
    tourn_link = str(html_table_to_dict_list(url, hrefed=True, stop=tourn_name)[0]['Tournament Link'])
    tourn_id = link_split(tourn_link, 'tourn_id=')
    return tourn_id

def get_event_id(event, tourn_id):
    events_tab_link = "https://www.tabroom.com/index/tourn/fields.mhtml?tourn_id="+tourn_id
    events_tab_html = requests.get(events_tab_link).text
    soup = BeautifulSoup(events_tab_html, 'html.parser')
    events = soup.find('div', {'class': 'sidenote'})
    for a in events.find_all('a'):
        a_name = clean_html(a.get_text())
        if type(event) == list:
            for name in event:
                if a_name == name:
                    event_id = link_split(a.get('href'), 'event_id=')
                    return event_id
        else:
            if a_name == event:
                event_id = link_split(a.get('href'), 'event_id=')
                return event_id

def get_category_id(category_name, tourn_id):
    category_tab_link = "https://www.tabroom.com/index/tourn/judges.mhtml?tourn_id="+tourn_id
    category_tab_html = requests.get(category_tab_link).text
    soup = BeautifulSoup(category_tab_html, 'html.parser')
    categories = soup.find('div', {'class': 'sidenote'})
    for div in categories.find_all('div', {'class': 'odd nospace'}):
        category_name = clean_html(div.find('span', {'class': 'third semibold bluetext'}).get_text())
        if type(category_name) == list:
            for name in category_name:
                if category_name == name:
                    judges_link = div.find('a', {'class': 'blue full centeralign padno padvertless'}).get('href')
                    category_id = link_split(judges_link, 'category_id=').split('&tourn_id=')[0]
                    return category_id
        else:
            if category_name == category_name:
                judges_link = div.find('a', {'class': 'blue full centeralign padno padvertless'}).get('href')
                category_id = link_split(judges_link, 'category_id=').split('&tourn_id=')[0]
                return category_id

def get_judge_paradigm(judge_name, category_id, tournament_id):
    judges_page = f"https://www.tabroom.com/index/tourn/judges.mhtml?category_id={category_id}&tourn_id={tournament_id}"
    judges_dict = html_table_to_dict_list(page_link=judges_page, hrefed=True)
    for judge in judges_dict:
        full_name = ""
        if judge['Middle'] == '':
            full_name = f"{judge['First']} {judge['Last']}"
        else:
            full_name = f"{judge['First']} {judge['Middle']} {judge['Last']}"
        judge['Full Name'] = full_name
    for judge in judges_dict:
        if judge['Full Name'] == judge_name:
            paradigm_page = judge['Paradigm']
            paradigm_html = requests.get(paradigm_page).text
            paradigm_soup = BeautifulSoup(paradigm_html, 'html.parser')
            paradigm_div = paradigm_soup.find('div', {'class': 'paradigm ltborderbottom'})
            paradigm_content = paradigm_div.find_all('p')
            for paragraph in range(len(paradigm_content)):
                paradigm_content[paragraph] = paradigm_content[paragraph].get_text()
            return paradigm_content