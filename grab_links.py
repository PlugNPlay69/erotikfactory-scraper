import requests
import multiprocessing
from bs4 import BeautifulSoup
from tqdm import tqdm


def cook(content):
    return BeautifulSoup(content, "html.parser")


def request_page(i):
    # sorted by article number, using 1000 for n_articles but max seems to be 100 internally
    r = requests.get(f"https://erotikfactory.ch/Dildos_s{i}?Sortierung=7&af=1000")
    r.raise_for_status()

    return r.content


def get_n_products(soup):
    bar = soup.find(id="result-wrapper").find("hr").find_previous_sibling()
    n_products = list(bar.children)[1].text
    n_products = int(n_products.split()[-1])
    return n_products


def extract_links(soup):
    product_list = soup.find(id="product-list")
    for div in product_list:
        url = div.find("meta", itemprop="url")['content']
        yield url


def extract_links_from_page(i):
    return list(extract_links(cook(request_page(i))))


def writelines(file, lines):
    file.writelines(line + "\n" for line in lines)  # god python is so fucking stupid


if __name__ == '__main__':
    # first page done manually to also get the total number of products/pages
    soup = cook(request_page(1))
    n_products = get_n_products(soup)
    links = list(extract_links(soup))
    n_pages = n_products // len(links)
    pages = range(2, n_pages + 1)

    with open("product_links.txt", "wt") as links_file:
        writelines(links_file, links)  # first page results

        with multiprocessing.Pool() as pool:
            for links in tqdm(pool.imap_unordered(extract_links_from_page, pages), initial=1, total=n_pages):
                writelines(links_file, links)
