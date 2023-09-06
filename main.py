from datetime import date, datetime, timedelta
import os
import requests

from bs4 import BeautifulSoup, Tag
from requests_oauthlib import OAuth1

from models import Keyword, JerkChickenMeal, Setting, JerkChickenEntry

API_KEY = os.environ["API_KEY"]
API_SECRET = os.environ["API_SECRET"]
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
ACCESS_SECRET = os.environ["ACCESS_SECRET"]

BASE_URL = "https://dining.columbia.edu"
KEYWORDS_URL = "https://dining.columbia.edu/json/keywords"
TWITTER_URL = "https://api.twitter.com/2/tweets"

THE_WORST = "jerk chicken"
DINING_HALLS = ["Grace Dodge", "Faculty House", "Fac Shack", "Ferris", "JJ's", "Chef Don's", "Chef Mike's", "John Jay"]

def _hook_keyword(obj):
    try:
        return Keyword(**obj)
    except TypeError:
        return obj

def get_menu_keywords() -> list[Keyword]:
    raw_keywords = requests.get(KEYWORDS_URL)
    if raw_keywords.status_code != 200:
        raw_keywords.raise_for_status()
    keywords: list[Keyword] = raw_keywords.json(object_hook=_hook_keyword)
    return [kw for kw in keywords if kw.type == "cu_dining_menu"]

def get_menu_hall(menu_keyword: Keyword) -> str | None:
    for hall in DINING_HALLS:
        if hall.lower() in menu_keyword.title.lower():
            return hall
    return None

def filter_dining_halls(menu_keywords: list[Keyword]) -> list[Keyword]:
    return [kw for kw in menu_keywords if get_menu_hall(kw) is not None]

def get_page_html(path: str) -> BeautifulSoup:
    print(BASE_URL + path)
    res = requests.get(BASE_URL + path)
    if res.status_code != 200:
        res.raise_for_status()
    return BeautifulSoup(res.text, "html.parser")

def get_menu_date_ranges(soup: BeautifulSoup) -> list[Tag]:
    return soup.find_all(class_="paragraph--type--cu-dining-date-range")

def is_menu_date_in_range(soup: BeautifulSoup, target_date: date) -> bool:
    menu_date_range = get_menu_date_ranges(soup)[0]
    get_date = lambda tag: datetime.strptime(tag.find("time").get("datetime"), "%Y-%m-%dT%H:%M:%SZ").date()
    menu_start_date: date = get_date(menu_date_range.find(class_="field--name-field-cu-dining-date-from"))
    menu_end_date: date = get_date(menu_date_range.find(class_="field--name-field-cu-dining-date-to"))
    return menu_start_date == target_date and (menu_end_date == target_date or menu_end_date == target_date + timedelta(days=1))

def get_offending_meals_for_date_range(date_range: Tag) -> list[JerkChickenMeal]:
    res: list[JerkChickenMeal] = []
    meal_infos: list[Tag] = date_range.find_all("paragraph--type--cu-dining-meal")
    for meal_info in meal_infos:
        meal_name = meal_info.find(class_="field--name-field-cu-title").find(class_="field--item").get_text().strip()
        if THE_WORST in meal_name.lower():
            res.append(JerkChickenMeal(meal_name, True))
        elif (meal_desc_tag := meal_info.find(class_="field--name-field-cu-dining-meal-text")) is not None:
            meal_desc = meal_desc_tag.find(class_="field--item").get_text()
            if THE_WORST in meal_desc.lower():
                res.append(JerkChickenMeal(meal_name, False))
    return res

def get_menu_meal_of_day(date_range: Tag) -> str:
    return date_range.find(class_="field--name-field-cu-dining-menu-type").find("a").get_text()

def get_offending_meals(menu_keywords: list[Keyword], target_date: date) -> list[JerkChickenEntry]:
    res: list[JerkChickenEntry] = []
    visited_halls: set[str] = set()
    for kw in menu_keywords:
        hall = get_menu_hall(kw)
        assert hall is not None
        print(f"{hall=} {visited_halls=}")
        if hall in visited_halls:
            print("Skipping")
            continue
        soup = get_page_html(kw.path)
        if not is_menu_date_in_range(soup, target_date):
            continue

        menu_date_ranges = get_menu_date_ranges(soup)
        for date_range in menu_date_ranges:
            offending_meals_for_date_range = get_offending_meals_for_date_range(date_range)
            if offending_meals_for_date_range:
                menu_meal_of_day = get_menu_meal_of_day(date_range)
                menu_setting = Setting(hall, menu_meal_of_day)
                res.append(JerkChickenEntry(offending_meals_for_date_range, menu_setting))
            
        visited_halls.add(hall)

    return res

def get_tweet(offending_meals: list[JerkChickenEntry], target_date: date):
    the_date = "%d/%d/%d" % (target_date.month, target_date.day, target_date.year)

    if not offending_meals:
        """
        No jerk chicken today (2/6/23)
        """
        return '\N{white heavy check mark} No jerk chicken today (%s)' % (the_date)
    
    """
    Jerk chicken today (2/6/23)

        - Jerk Chicken at John Jay for lunch
        - Jerk Chicken Sub at Chef Mike's
        ...
    """

    msg = ["\N{Police Cars Revolving Light} Jerk chicken today (%s)\n" % (the_date)]

    for entry in offending_meals:
        meal_names = [m.food_name for m in entry.meals]
        listed_meals: str = ""
        if len(meal_names) == 1:
            listed_meals = meal_names[0]
        elif len(meal_names) == 2:
            listed_meals = " and ".join(meal_names)
        else:
            # len(meal_names) > 2
            listed_meals = "%s, and %s" % (", ".join(meal_names[:-1]), meal_names[-1])

        line = "\N{Poultry Leg} %s at %s for %s" % (listed_meals, entry.setting.dining_hall, entry.setting.meal_of_day)
        msg.append(line)

    return "\n".join(msg)

def main(event, context):
    menu_keywords = get_menu_keywords()
    dining_hall_menus = filter_dining_halls(menu_keywords)
    
    today = datetime.today().date()
    offending_meals = get_offending_meals(dining_hall_menus, today)
    tweet = get_tweet(offending_meals, today)

    res = requests.post(
        auth=OAuth1(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET), 
        url="https://api.twitter.com/2/tweets", 
        json={"text": tweet}
    )
    if res.status_code != 201:
        res.raise_for_status()
