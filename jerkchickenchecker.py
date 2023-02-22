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
        food_name = html.unescape(food["title"]).strip()
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
    def meal_of_day_to_num(meal_of_day):
        if meal_of_day == "Breakfast":
            return 0
        elif meal_of_day == "Lunch":
            return 1
        else:
            # Dinner
            return 2

    def num_to_meal_of_day(num):
        if num == 0:
            return "Breakfast"
        elif num == 1:
            return "Lunch"
        else:
            # 2
            return "Dinner"

    the_date = "%d/%d/%d" % (the_date.month, the_date.day, the_date.year)

    if not chicken_meals:
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

        msg = ["\N{Police Cars Revolving Light} Jerk chicken today (%s)\n" % (the_date)]

        grouped_chicken_meals = {}
        for m in chicken_meals:
            location, meal = m

            details = []

            # Get dining hall
            for hall in ["John Jay", "Ferris", "JJs", "Chef Don's", "Chef Mike's"]:
                if hall in location:
                    details.append(hall)
                    break

            if len(details) != 1:
                raise RuntimeError("error finding dining hall")

            # Some dining halls have multiple meals a day. With these, add the meal of day.
            if details[0] in ["John Jay", "Ferris"]:
                for meal_of_day in ["Breakfast", "Lunch", "Dinner"]:
                    if meal_of_day in location:
                        details.append(meal_of_day_to_num(meal_of_day))
                        break
                    
                if len(details) != 2:
                    raise RuntimeError("error finding meal of day")

            details = tuple(details)
            meal = jerk_chicken_dict[meal]
            if details not in grouped_chicken_meals:
                grouped_chicken_meals[details] = [meal]
            elif meal not in grouped_chicken_meals[details]:
                grouped_chicken_meals[details].append(meal)

            # info.append(f" - {jerk_chicken_dict[meal]} at {location_with_time}")
        
        curr_hall = None
        for meal_details in sorted(grouped_chicken_meals):
            location = ""
            if len(meal_details) == 1:
                location = meal_details[0]
            else:
                # len(meal_details) == 2
                location = "%s for %s" % (meal_details[0], num_to_meal_of_day(meal_details[1]).lower())

            # getting grammatically-correct comma list
            meals = grouped_chicken_meals[meal_details]
            meals = list(sorted(meals))
            listed_meals = ""
            if len(meals) == 1:
                listed_meals = meals[0]
            elif len(meals) == 2:
                listed_meals = " and ".join(meals)
            else:
                # len(meals) > 2
                listed_meals = "%s, and %s" % (", ".join(meals[:-1]), meals[-1])

            line = "\N{Poultry Leg} %s at %s" % (listed_meals, location)

            if curr_hall != meal_details[0]:
                if curr_hall:
                    line = "\n" + line
                curr_hall = meal_details[0]

            msg.append(line)

        return "\n".join(msg)

def main(event, context):
    foods = requests.get(FOOD_URL)
    if foods.status_code != 200:
        foods.raise_for_status()

    jerk_chicken_dict = get_chicken_dict(foods.json())

    menus = requests.get(MENU_URL)
    if menus.status_code != 200:
        menus.raise_for_status()

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
        res.raise_for_status()
