import logging
import azure.functions as func
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

def is_same_domain(url, base_domain):
    parsed_url = urlparse(url)
    return base_domain in parsed_url.netloc

def crawl_and_return_content(start_url):
    base_domain = urlparse(start_url).netloc
    visited_urls = set()
    urls_to_visit = [start_url]
    accumulated_content = ""

    while urls_to_visit:
        current_url = urls_to_visit.pop(0)
        if current_url in visited_urls:
            continue

        try:
            response = requests.get(current_url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract text content from the page
            text_content = soup.get_text(separator='\n', strip=True)
            accumulated_content += f"Content from {current_url}:\n{text_content}\n\n"

            visited_urls.add(current_url)

            # Find and add new URLs
            for link in soup.find_all('a', href=True):
                new_url = urljoin(current_url, link['href'])
                if new_url not in visited_urls and is_same_domain(new_url, base_domain):
                    urls_to_visit.append(new_url)

        except requests.RequestException as e:
            logging.error(f"Error fetching {current_url}: {e}")

    return accumulated_content

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    start_url = req.params.get('url')

    if not start_url:
        return func.HttpResponse(
            "Please pass a URL on the query string",
            status_code=400
        )

    content = crawl_and_return_content(start_url)
    return func.HttpResponse(content, mimetype="text/plain", charset='utf-8')
