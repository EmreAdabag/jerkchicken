import requests
import html
from datetime import datetime
import tweepy
import json

from keys import api_key, api_secret, bearer_token, access_token, access_token_secret

FOOD_URL = "https://dining.columbia.edu/cu_dining/rest/meals"
MENU_URL = "https://dining.columbia.edu/cu_dining/rest/menus/nested"


def log_error(message):
    with open("errorlog.txt", "a") as f:
        f.write(f"{datetime.now().strftime('%m/%d/%Y, %H:%M:%S')} {message}\n\n")


def get_chicken_dict() -> dict[str, str]:
    foods = requests.get(FOOD_URL)
    if foods.status_code != 200:
        log_error("error fetching chicken dict")
        exit()

    foods_json = foods.json()
    jerk_chicken_dict = {}

    for food in foods_json:
        food_name = html.unescape(food["title"])
        if "jerk chicken" in food_name.lower():
            jerk_chicken_dict[food["nid"]] = food_name

    return jerk_chicken_dict


def get_menus():
    menus = requests.get(MENU_URL)
    print(menus.status_code)
    if menus.status_code != 200:
        log_error("error fetching menu")
        exit()

    return menus.json()
    

def get_chicken_meals(jerk_chicken_dict: dict[str, str], menus_json: list, target_date):
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


def get_chicken_message(jerk_chicken_dict, chicken_meals):

    if len(chicken_meals) == 0:
        """
        No jerk chicken today
        """
        msg = '\N{white heavy check mark} No jerk chicken today'

    else:
        """
        Jerk chicken today!

         - Jerk Chicken at John Jay for lunch
         - Jerk Chicken Sub at Chef Mike's
         ...
        """

        msg = ["\N{Police Cars Revolving Light} Jerk chicken today!\n"]
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

            msg.append(f" - {jerk_chicken_dict[meal]} at {location_with_time}")
        
    return msg


def tweet(message: str):
    try:
        auth = tweepy.OAuthHandler(keys.api_key, keys.api_secret)
        auth.set_access_token(keys.access_token, keys.access_token_secret)
        tweepy.API(auth).update_status(message)
    except tweepy.TweepyException as e:
        log_error(e)
        exit()



def main():

    jerk_chicken_dict = get_chicken_dict()
    menus = get_menus()

    chicken_meals = get_chicken_meals(jerk_chicken_dict, menus, datetime.today().date())
    
    msg = get_chicken_message(jerk_chicken_dict, chicken_meals)

    tweet("\n".join(msg))



if __name__ == '__main__':
    main()
