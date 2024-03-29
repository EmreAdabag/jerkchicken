from datetime import datetime
import os
import re

from bs4 import BeautifulSoup
import requests
from requests_oauthlib import OAuth1

from models import *

API_KEY = os.environ["API_KEY"]
API_SECRET = os.environ["API_SECRET"]
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
ACCESS_SECRET = os.environ["ACCESS_SECRET"]

BASE_URL = "https://dining.columbia.edu"
KEYWORDS_URL = "https://dining.columbia.edu/json/keywords?_format=json"
TWITTER_URL = "https://api.twitter.com/2/tweets"

THE_WORST = r'jerk chicken'
# DINING_HALLS = ["Grace Dodge", "Faculty House", "Fac Shack", "Ferris", "JJ's", "Chef Don's", "Chef Mike's", "John Jay"]
DINING_HALLS = ["Ferris", "John Jay", "JJ's"]
# ["ferris", "john-jay", ...], i.e., what would show up in a path
DINING_HALL_PATHS = ["ferris", "john-jay", "jjs"]
assert len(DINING_HALLS) == len(DINING_HALL_PATHS)

def find_meal_with_matching_time_of_day(meals, time_of_day):
    for meal in meals:
        if meal.time_of_day == time_of_day:
            return meal
    return None

def get_offending_meals(text) -> list[JerkChickenMeal]:
    """
    Given HTML text, return list of offending meals as JerkChickenMeal objects
    """
    soup = BeautifulSoup(text, 'lxml')
    offending_meals = []
    
    matches = soup.find_all('div', class_='paragraph paragraph--type--cu-dining-date-range paragraph--view-mode--default anchored')
    for meal in matches:
        time_of_day = meal.find('div', class_='field field--name-field-cu-dining-menu-type field--type-entity-reference field--label-above').find('div', class_="field--item").text
        sections = meal.find_all('div', class_='accordion field field--name-field-cu-title field--type-string field--label-above')
        for section in sections:
            no_whitespace = ''.join(str(section.text).split('\n')).replace('Title', '')
            if bool(re.search(THE_WORST, no_whitespace, re.IGNORECASE)):
                meal_for_time_of_day = find_meal_with_matching_time_of_day(offending_meals, time_of_day)
                if meal_for_time_of_day is not None:
                    meal_for_time_of_day.food_names.append(no_whitespace)
                else:
                    offending_meals.append(JerkChickenMeal(food_names=[no_whitespace], time_of_day=time_of_day))
 
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

def join_into_comma_list(words: list[str]):
    assert words
    if len(words) == 1:
        return words[0]
    elif len(words) == 2:
        return " and ".join(words)
    else:
        # len(words) > 2
        return f"{', '.join(words[:-1])}, and {words[-1]}"

def construct_tweet(offending_meals: list[JerkChickenEntry], date):
    the_date = date.strftime("%b %d, %Y")

    if not offending_meals:
        """
        ✅ No jerk chicken today (Feb 6, 2023)
        """
        return f"\N{white heavy check mark} No jerk chicken today ({the_date})"
    
    """
    🚨 Jerk chicken today (Feb 6, 2023)

    At John Jay:
    🍗 Jerk Chicken for lunch
    🍗 Jerk Chicken and Jerk Chicken Wrap for dinner
    ...
    """

    msg = [f"\N{Police Cars Revolving Light} Jerk chicken today ({the_date})\n"]

    for entry in offending_meals:
        msg.append(f"At {entry.dining_hall}:")
        for meal in entry.meals:
            meals_comma_list = join_into_comma_list(meal.food_names)
            line = (f"\N{Poultry Leg} {meals_comma_list} for {meal.time_of_day.lower()}")
            msg.append(line)

    return "\n".join(msg)

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
            offending_meal_entries.append(JerkChickenEntry(dining_hall=menu.dining_hall, meals=offending_meals))

    tweet = construct_tweet(offending_meal_entries, today)
    res = requests.post(
        auth=OAuth1(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET),
        url=TWITTER_URL,
        json={"text": tweet}
    )
    if res.status_code != 201:
        res.raise_for_status()

if __name__ == "__main__":
    main(None, None)
