import json
import multiprocessing

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import sys


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def parse_product(soup):
    offer = soup.find(id="product-offer")

    # first child is gallery, second prod info
    inner_prod_info = list(offer.children)[1].div

    desc = inner_prod_info.find(itemprop="description")
    features = desc.ul.extract()
    prod = {"title": inner_prod_info.find(itemprop="name").text,
            "sku": int(inner_prod_info.find(itemprop="sku").text),
            "category": inner_prod_info.find(itemprop="category").text,
            "brand": inner_prod_info.find(itemprop="brand").find(itemprop="name").text,
            "full_description": desc.text,
            "description": desc.text,
            "features": [li.text for li in features.find_all("li")]}

    return prod


def get_soup(url):
    r = requests.get(url)
    r.raise_for_status()

    return BeautifulSoup(r.content, "html.parser")


def extract_product(url):
    product = {
        "url": url,
        "error_type": None,
    }

    soup = None
    try:
        soup = get_soup(url)
        product.update(parse_product(soup))
    except Exception as e:
        # eprint(f"Failed to process {url}.", e)
        product["error_type"] = "request" if soup is None else "parsing"
        product["error"] = str(e)
        return product

    return product


if __name__ == '__main__':
    with open("product_links.txt") as file:
        urls = [line.strip() for line in file.readlines()]

    with open("products.json", "wt") as product_file:
        product_file.write("[\n")
        with multiprocessing.Pool() as pool:
            start = True
            for product in (pbar := tqdm(pool.imap_unordered(extract_product, urls), total=len(urls))):
                pbar.set_description(product.get("title", product.get("error", "WTF?!")))
                if start:
                    start = False
                else:
                    product_file.write(",\n")

                json.dump(product, product_file, indent=2)
        product_file.write("]\n")
