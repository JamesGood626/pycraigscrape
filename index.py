from time import sleep
from bs4 import BeautifulSoup
import requests

# submitted from UI/CMD Line as user input
user_selected_gigs = ["web-html-info-design"]
search_terms = ["javascript", "JavaScript", "JS", "HTML", "CSS"]
cities = ["newyork"]

# How the names should appear in the UI
# "Systems / Networking"
# "Software/QA/DBA"
# "Web / Info Design"
# "Computer Gigs"
gig_sections = {
    "systems-networking": lambda city: f'https://{city}.craigslist.org/d/systems-networking/search/sad',
    "software-qa-dba-etc": lambda city: f'https://{city}.craigslist.org/d/software-qa-dba-etc/search/sof',
    "web-html-info-design": lambda city: f'https://{city}.craigslist.org/d/web-html-info-design/search/web',
    "computer-gigs": lambda city: f'https://{city}.craigslist.org/d/computer-gigs/search/cpg',
}


def get_html_page(link, path=None, first_request=False):
    full_path = f"scraped/{path}" if path else False
    try:
        return open_saved_html(full_path)
    except:
        # Moved sleep here from outside of get_craigslist_city_pages
        # to avoid needing to sleep if the html_page is already saved locally.
        if not first_request:
            sleep(5)
        return request_html_page_and_write(link, full_path)


def open_saved_html(full_path):
    if not full_path:
        raise "no full path provided"
    f = open(full_path, 'r')
    soup = BeautifulSoup(f.read(), 'html.parser')
    return soup


def request_html_page_and_write(link, full_path=False):
    """
      When fetching the gig listing pages we don't want to save
      the html associated with the listing locally, so we don't pass
      in a full_path for a directory/filename.html.
    """
    r = requests.get(link)
    if full_path:
        f = open(full_path, 'wb')
        f.write(r.content)
    soup = BeautifulSoup(r.content, 'html.parser')
    return soup


def find_matching_links(soup, cities):
    """
        orig_str = "https://tunis.craigslist.org/"
        s.split("//")
        ['https:', 'tunis.craigslist.org/']
        orig_str # Remains unmutated
        'https://tunis.craigslist.org/'
        'tunis.craigslist.org/'.split(".")
        ['tunis', 'craigslist', 'org/']
    """
    links = []
    for link in soup.find_all('a'):
        link_url = link.get('href')
        # There was a None mixed in there
        if isinstance(link_url, str):
            end_link = link_url.split("//")[-1]
            city = end_link.split(".")[0]
            if city in cities:
                links.append((city, link_url))
    return links


def get_craigslist_city_pages(links):
    pages = []
    for idx, (city, link_url) in enumerate(links):
        page = get_html_page(link_url, f'{city}.html', idx == 0)
        pages.append(page)
    return pages


# ***********************
# Only the functions below are being used for the program.
# Everything else will just serve for later reference.
# ***********************
def get_gigs_pages(cities, user_selected_gigs):
    """
        Returns a list of gig page html
    """
    gig_pages = []
    for city in cities:
        for idx, gig in enumerate(user_selected_gigs):
            gig_url = gig_sections[gig](city)
            page = get_html_page(gig_url, f'{city}-{gig}.html', idx == 0)
            gig_pages.append(page)
    return gig_pages


def get_gig_listing_details(gig_pages, search_terms):
    gig_listing_pages = []
    for gig in gig_pages:
        a_tags = gig.select_one('.content').find_all('a')
        for idx, link in enumerate(a_tags):
            link_url = link.get('href')
            if link_url == "#":
                continue
            else:
                # We've got a valid link... open the page,
                # but we aren't saving these pages.
                gig_listing_page = get_html_page(
                    link_url, first_request=(idx == 0))
                details = extract_details(
                    gig_listing_page, search_terms, link_url)
                if details != False:
                    gig_listing_pages.append(details)
    return gig_listing_details


def extract_details(gig_listing_page, search_terms, link_url):
    """
        Only append those which contain a postingtitle/postingbody text
        match of the user inputted job search terms...

        Can't access contact_email without clicking the .reply-button
        Next best thing is to just return the link_url associated w/ the listing.
        Otherwise selenium will be necessary to retrieve the email.
        contact_email = gig_listing_page.select_one('.reply-email-address')

        Listing page ids/classes to grab:
            IOS & Android Developer with Java AWS experience <- prime for regexing up
            w/ the user's provided input hopefully...)
        - #postingbody (section tag, which contains text of the listing, but also I see a div in there as well. Only
            checked one listing.. so we'll see if it poses an issue)
        - .reply-email-address (p tag w/ a nested a tag which contains the contact email)
            OR
        .mailapp <- class on the a tag which is nested in the p tag.
    """
    title = gig_listing_page.select_one('#titletextonly').text
    body = gig_listing_page.select_one('#postingbody').text

    search_match = True
    for search_term in search_terms:
        # search_term matching should be more robust than this.
        search_match = search_term in title
        search_match = search_term in body

    if not search_match:
        return False
    print("extract_details returning")
    print((title, body, link_url))
    return (title, body, link_url)


gig_pages = get_gigs_pages(cities, user_selected_gigs)
gig_listing_details = get_gig_listing_details(gig_pages, search_terms)
# Program displays/sends JSON of gig_details and terminates.
print("the gig_listing_details")
print(gig_listing_details)


# Thought these would all be necessary... but it turned out they weren't
# home_page_html = get_html_page('https://www.craigslist.org/about/sites', "home_page.html", first_request=True)
# links = find_matching_links(home_page_html, cities)
# city_pages = get_craigslist_city_pages(links)
# get_gigs_links(city_pages)
