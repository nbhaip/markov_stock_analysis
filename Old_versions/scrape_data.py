from bs4 import BeautifulSoup
import requests
import sys

URL_part_1 = "https://finance.yahoo.com/quote/"
URL_part_2 = "/history"
PARSER = "html.parser"


def get_page_content(name):
    try:
        page = requests.get(URL_part_1+name+URL_part_2)
    except requests.exceptions.RequestException as e:
        print(e)
        sys.exit(1)
    return BeautifulSoup(page.content, PARSER)


def main():
    content = get_page_content("goog")
    print(content)

if __name__ == "__main__":
    main()