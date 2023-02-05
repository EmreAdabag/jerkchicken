import requests
from datetime import datetime
import tweepy
import keys

FOOD_URL = "https://dining.columbia.edu/cu_dining/rest/meals"
MENU_URL = "https://dining.columbia.edu/cu_dining/rest/menus/nested"

def get_chicken_dict() -> dict[str, str]:
    foods_json = requests.get(FOOD_URL).json()
    jerk_chicken_dict = {}

    for food in foods_json:
        if "jerk chicken" in food["title"].lower():
            jerk_chicken_dict[food["nid"]] = food["title"]

    return jerk_chicken_dict

def get_chicken_meals(jerk_chicken_dict: dict[str, str]):
    chicken_days = []
    today = datetime.today().date()

    menus_json = requests.get(MENU_URL).json()

    for menu in menus_json:

        # some dining halls have multiple meals a day (breakfast, lunch, dinner)
        for meal_of_day in menu["date_range_fields"]:
            date_from = meal_of_day["date_from"]

            if datetime.strptime(date_from, '%Y-%m-%dT%H:%M:%S').date() != today:
                continue

            location = meal_of_day["title"]

            for station in meal_of_day["stations"]:
                for meal in station["meals"]:
                    if meal in jerk_chicken_dict:
                        chicken_days.append((location, meal))

    return chicken_days

def tweet(message: str):
    auth = tweepy.OAuthHandler(keys.api_key, keys.api_secret)
    auth.set_access_token(keys.access_token, keys.access_token_secret)
    tweepy.API(auth).update_status(message)

def main():
    jerk_chicken_dict = get_chicken_dict()
    chicken_meals = get_chicken_meals(jerk_chicken_dict)

    if len(chicken_meals) == 0:
        """
        No jerk chicken today
        """

        tweet('\N{white heavy check mark} No jerk chicken today')
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

        tweet("\n".join(msg))

if __name__ == '__main__':
    main()
