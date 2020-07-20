import os

import htmlmin
import requests
import requests_cache

from bs4 import BeautifulSoup
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
            f.write(htmlmin.minify(template_path.render(kwargs)))


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
            if cell.a:
                row_obj["hrefs"][headings[ptr]] = cell.a["href"]
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
        (h.text, h.a["href"].split("/")[-1] if h.a else h.text) for h in headings[3:-2]
    ]

    fullheadings = pre_headings + [p[1] for p in problems] + post_headings

    table_data = parse_table(results_parsed.table, fullheadings, 2)
    return {
        "problems": problems,
        "results": table_data,
    }


def parse_num(n):
    if n == "–":
        return 0
    try:
        return int(n)
    except:
        try:
            return float(n)
        except:
            print(n)
            assert 1 == 0


def render_results(year):
    results_data = get_results(year)
    problems = results_data["problems"]
    num_per_day = len(problems) // 2
    day1_problems = problems[:num_per_day]
    day2_problems = problems[num_per_day:]
    for row in results_data["results"]:
        row["country"] = row["hrefs"]["country"].split("/")[-1]
        day1_score = 0
        for p in day1_problems:
            day1_score += parse_num(row[p[1]])
        day2_score = 0
        for p in day2_problems:
            day2_score += parse_num(row[p[1]])
        row["day1_score_abs"] = (
            int(day1_score)
            if float(day1_score).is_integer()
            else format(day1_score, ".2f")
        )
        row["day2_score_abs"] = (
            int(day2_score)
            if float(day2_score).is_integer()
            else format(day2_score, ".2f")
        )

    for day in [("day1", "Day 1"), ("day2", "Day 2"), ("overall", "Overall")]:
        renderer.render(
            f"results/{year}-{day[0]}.html",
            "results.html",
            year=year,
            day1_problems=day1_problems,
            day2_problems=day2_problems,
            results=results_data["results"],
            day=day[1],
        )


if __name__ == "__main__":
    # add arg to clear cache
    requests_cache.install_cache("ioi_cache")
    root = os.path.dirname(os.path.abspath(__file__))
    site_dir = os.path.join(root, "docs")
    templates_dir = os.path.join(root, "templates")
    env = Environment(loader=FileSystemLoader(templates_dir))
    renderer = Renderer(env, templates_dir, site_dir)

    print("Rendering index... ")
    oly_list = scrape_olympiad_list()
    renderer.render("index.html", "index.html", olympiads=oly_list)

    for oly in oly_list:
        print(f"Rendering {oly['year']} results...")
        render_results(oly["year"])

    print("Done")
