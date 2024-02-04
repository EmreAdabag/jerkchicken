from datetime import datetime
import re
from bs4 import BeautifulSoup
import requests
from requests_oauthlib import OAuth1

from models import *

# API_KEY = os.environ["API_KEY"]
# API_SECRET = os.environ["API_SECRET"]
# ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
# ACCESS_SECRET = os.environ["ACCESS_SECRET"]

BASE_URL = "https://dining.columbia.edu"
KEYWORDS_URL = "https://dining.columbia.edu/json/keywords?_format=json"
TWITTER_URL = "https://api.twitter.com/2/tweets"

THE_WORST = r'jerk ?chicken'
# DINING_HALLS = ["Grace Dodge", "Faculty House", "Fac Shack", "Ferris", "JJ's", "Chef Don's", "Chef Mike's", "John Jay"]
DINING_HALLS = ["Ferris", "John Jay"]
# ["ferris", "john-jay"], i.e., what would show up in a path
DINING_HALL_PATHS = [dh.lower().replace(" ", "-") for dh in DINING_HALLS]


# Given path, return if theres Jerk Chicken and what meal

def get_offending_meals(text) -> list[JerkChickenMeal]:
    """
    Given HTML text, return list of offending meals as JerkChickenMeal objects
    """
    # response = requests.get(BASE_URL + path)
    soup = BeautifulSoup(text, 'lxml')
    offending_meals = []
    
    matches = soup.find_all('div', class_='paragraph paragraph--type--cu-dining-date-range paragraph--view-mode--default anchored')
    for meal in matches:
        meal_of_day = meal.find('div', class_='field field--name-field-cu-dining-menu-type field--type-entity-reference field--label-above').find('div', class_="field--item").text
        sections = meal.find_all('div', class_='accordion field field--name-field-cu-title field--type-string field--label-above')
        for section in sections:
            no_whitespace = ''.join(str(section.text).split('\n')).replace('Title', '')
            if bool(re.search(THE_WORST, no_whitespace, re.IGNORECASE)):
                offending_meals.append(JerkChickenMeal(meal_name=no_whitespace, meal_of_day=meal_of_day))
 
    return offending_meals

def get_dining_menus(keywords) -> list[Keyword]:
    """
    Given a JSON of Dining API keywords, converts them to a list of Keyword objects
    and keeps only those whose type is cu_dining_menu.
    """
    keywords = [Keyword(**kw) for kw in keywords]
    return [kw for kw in keywords if kw.type == "cu_dining_menu"]

def get_date_combos(date) -> list[str]:
    """
    If today is 02-03-24, returns ["2-3-24", "2-03-24", "02-3-24", "02-03-24"]
    (order not important). The Dining API uses these date formats interchangeably
    in their path names.
    """
    month, day, year = date.month, date.day, date.year
    month, day, year = str(month), str(day), str(year)[-2:]
    res = []
    for m in [month, f"{month:0>2}"]:
        for d in [day, f"{day:0>2}"]:
            res.append(f"{m}-{d}-{year}")
    return res

def get_menus_for_date_and_halls(menus: list[Keyword], date) -> list[Menu]:
    """
    Given a list of menus (represented as Keywords), keeps only those whose
    date matches what is specified and dining hall exists in DINING_HALLS.

    The date and dining hall are checked by looking at the keyword's path.
    """
    date_combos = get_date_combos(date)

    menus_for_date = []
    # Filter dates
    for menu in menus:
        for date in date_combos:
            if date in menu.path:
                menus_for_date.append(menu)
                break

    menus_for_date_and_halls = []
    # Filter dining halls
    for menu in menus_for_date:
        for dh, dh_path in zip(DINING_HALLS, DINING_HALL_PATHS):
            if dh_path in menu.path:
                menus_for_date_and_halls.append(Menu(dining_hall=dh, path=menu.path))
                break

    return menus_for_date_and_halls

# def get_tweet(offending_meals: list[JerkChickenEntry], target_date):
#     the_date = "%d/%d/%d" % (target_date.month, target_date.day, target_date.year)

#     if not offending_meals:
#         """
#         No jerk chicken today (2/6/23)
#         """
#         return '\N{white heavy check mark} No jerk chicken today (%s)' % (the_date)
    
#     """
#     Jerk chicken today (2/6/23)

#         - Jerk Chicken at John Jay for lunch
#         - Jerk Chicken Sub at Chef Mike's
#         ...
#     """

#     msg = ["\N{Police Cars Revolving Light} Jerk chicken today (%s)\n" % (the_date)]

#     for entry in offending_meals:
#         meal_names = [m.food_name for m in entry.meals]
#         listed_meals: str = ""
#         if len(meal_names) == 1:
#             listed_meals = meal_names[0]
#         elif len(meal_names) == 2:
#             listed_meals = " and ".join(meal_names)
#         else:
#             # len(meal_names) > 2
#             listed_meals = "%s, and %s" % (", ".join(meal_names[:-1]), meal_names[-1])

#         line = "\N{Poultry Leg} %s at %s for %s" % (listed_meals, entry.setting.dining_hall, entry.setting.meal_of_day)
#         msg.append(line)

#     return "\n".join(msg)

def main(event, context):
    keywords = requests.get(KEYWORDS_URL)
    if keywords.status_code != 200:
        keywords.raise_for_status()
    dining_menus = get_dining_menus(keywords.json())

    today = datetime.today().date()
    today_menus = get_menus_for_date_and_halls(dining_menus, today)
    assert len(today_menus) <= len(DINING_HALLS)

    offending_meal_entries = []
    for menu in today_menus:
        menu_page = requests.get(BASE_URL + menu.path)
        if menu_page.status_code != 200:
            menu_page.raise_for_status()
        offending_meals = get_offending_meals(menu_page.text)
        if offending_meals:
            offending_meal_entries.append(JerkChickenEntry(dining_hall=menu.dining_hall, meal=offending_meals))

    print(offending_meal_entries)

"""
    tweet = "Hello Columbia"

    res = requests.post(
        auth=OAuth1(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET), 
        url="https://api.twitter.com/2/tweets", 
        json={"text": tweet}
    )
    if res.status_code != 201:
        res.raise_for_status()
"""

main(None, None)
