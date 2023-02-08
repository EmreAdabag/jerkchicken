import os
import requests
import html
from datetime import datetime
from requests_oauthlib import OAuth1

API_KEY = os.environ["API_KEY"]
API_SECRET = os.environ["API_SECRET"]
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
ACCESS_SECRET = os.environ["ACCESS_SECRET"]

FOOD_URL = "https://dining.columbia.edu/cu_dining/rest/meals"
MENU_URL = "https://dining.columbia.edu/cu_dining/rest/menus/nested"
TWITTER_URL = "https://api.twitter.com/2/tweets"

def get_chicken_dict(foods_json):
    jerk_chicken_dict = {}

    for food in foods_json:
        food_name = html.unescape(food["title"])
        if "jerk chicken" in food_name.lower():
            jerk_chicken_dict[food["nid"]] = food_name

    return jerk_chicken_dict

def get_chicken_meals(jerk_chicken_dict, menus_json, target_date):
    chicken_days = []

    for menu in menus_json:

        # some dining halls have multiple meals a day (breakfast, lunch, dinner)
        for meal_of_day in menu["date_range_fields"]:
            date_from = meal_of_day["date_from"]

            if datetime.strptime(date_from, '%Y-%m-%dT%H:%M:%S').date() != target_date:
                continue

            location = meal_of_day["title"]

            for station in meal_of_day["stations"]:
                for meal in station["meals"]:
                    if meal in jerk_chicken_dict:
                        chicken_days.append((location, meal))

    return chicken_days

def get_tweet(jerk_chicken_dict, chicken_meals, the_date):
    the_date = "%d/%d/%d" % (the_date.month, the_date.day, the_date.year)

    if len(chicken_meals) == 0:
        """
        No jerk chicken today (2/6/23)
        """
        return '\N{white heavy check mark} No jerk chicken today (%s)' % (the_date)
    else:
        """
        Jerk chicken today (2/6/23)

         - Jerk Chicken at John Jay for lunch
         - Jerk Chicken Sub at Chef Mike's
         ...
        """

        info = ["\N{Police Cars Revolving Light} Jerk chicken today (%s)\n" % (the_date)]
        for m in chicken_meals:
            location, meal = m

            location_with_time = "a dining hall"  # default message

            # dining halls with multiple meals a day
            # gets both dining hall and meal of day
            for hall in ["John Jay", "Ferris"]:
                if hall in location:
                    for meal_of_day in ["Breakfast", "Lunch", "Dinner"]:
                        if meal_of_day in location:
                            location_with_time = "%s for %s" % (hall, meal_of_day.lower())
                            break
                    break

            # dining halls with one meal a day
            # gets only dining hall
            for hall in ["JJs", "Chef Don's", "Chef Mike's"]:
                if hall in location:
                    location_with_time = hall
                    break

            info.append(f" - {jerk_chicken_dict[meal]} at {location_with_time}")
        
        seen = set()
        msg = []

        # remove duplicates while maintaining order
        for line in info:
            if line not in seen:
                seen.add(line)
                msg.append(line)

        return "\n".join(msg)

def main(event, context):
    foods = requests.get(FOOD_URL)
    if foods.status_code != 200:
        raise RuntimeError("error fetching food items: " + foods.text)

    jerk_chicken_dict = get_chicken_dict(foods.json())

    menus = requests.get(MENU_URL)
    if menus.status_code != 200:
        raise RuntimeError("error fetching menu: " + menus.text)

    today = datetime.today().date()
    chicken_meals = get_chicken_meals(jerk_chicken_dict, menus.json(), today)

    tweet = get_tweet(jerk_chicken_dict, chicken_meals, today)
    payload = {"text": tweet}

    res = requests.post(
        auth=OAuth1(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET), 
        url=TWITTER_URL, 
        json=payload
    )
    if res.status_code != 201:
        raise RuntimeError("failed to post tweet '%s': %s" % (tweet, res.text))

if __name__ == "__main__":
    main(None, None)
