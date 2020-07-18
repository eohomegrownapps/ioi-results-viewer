import requests
from bs4 import BeautifulSoup
import os
from jinja2 import Environment, FileSystemLoader


class Renderer:
    def __init__(self, environment, templates_dir, site_dir):
        self.environment = environment
        self.templates_dir = templates_dir
        self.site_dir = site_dir

    def render(self, filename, templatename, **kwargs):
        site_path = os.path.join(site_dir, filename)
        template_path = env.get_template(templatename)
        with open(site_path, "w") as f:
            f.write(template_path.render(kwargs))


def parse_table(page, headings, skiprows=1):
    results = []
    row_cnt = 0
    for row in page:
        if row_cnt < skiprows:
            row_cnt += 1
            continue
        row_obj = {"hrefs": {}}
        ptr = 0
        for cell in row:
            # TODO: typecasting
            row_obj[headings[ptr]] = cell.text
            if cell.name == "a":
                row_obj["hrefs"]["f"] = cell["href"]
            ptr += 1
        results.append(row_obj)
    return results


def scrape_olympiad_list():
    olympiads_url = "https://stats.ioinformatics.org/olympiads/"
    olympiads_page = requests.get(olympiads_url)
    oly_parsed = BeautifulSoup(olympiads_page.text, "html.parser")

    headings = ["id", "year", "dates", "host", "city", "contestants", "countries"]
    return parse_table(oly_parsed.table, headings, 1)


def get_results(year):
    results_url = f"https://stats.ioinformatics.org/results/{year}"
    results_page = requests.get(results_url)
    results_parsed = BeautifulSoup(results_page.text, "html.parser")

    pre_headings = ["rank", "contestant", "country"]
    post_headings = ["score_abs", "score_rel", "medal"]
    headings = list(results_parsed.table.tr.children)

    problems = [
        (h.text, h.a["href"].split("/")[-1] if h.a else h.text)
        for h in headings[3:-2]
    ]

    fullheadings = pre_headings + [p[0] for p in problems] + post_headings

    table_data = parse_table(results_parsed.table, fullheadings, 2)
    return {
        "problems": problems,
        "results": table_data,
    }


if __name__ == "__main__":
    root = os.path.dirname(os.path.abspath(__file__))
    site_dir = os.path.join(root, "site")
    templates_dir = os.path.join(root, "templates")
    env = Environment(loader=FileSystemLoader(templates_dir))
    renderer = Renderer(env, templates_dir, site_dir)

    oly_list = scrape_olympiad_list()
    renderer.render("index.html", "index.html", olympiads=oly_list)

    print(get_results("2000"))
