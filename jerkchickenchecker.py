import requests
from datetime import datetime
import tweepy
import keys

jerk_chicken_dict = {367 : "jerk chicken",
6744: "jerk chicken roll",
5977: "jerk chicken sandwich",
3565: "jerk chicken wrap",
3585: "JJs jerk chicken quesadilla with tamarind sauce",
2355: "jerk chicken",
3626: "vegan jerk chicken"}

FOOD_URL = "https://dining.columbia.edu/cu_dining/rest/meals"
MENU_URL = "https://dining.columbia.edu/cu_dining/rest/menus/nested"

def get_chicken_meals():
    chicken_days = []
    today = datetime.today().date

    menus_json = requests.get(MENU_URL).json()

    for menu in menus_json:
        date_range_fields = menu["date_range_fields"][0]
        date_from = date_range_fields["date_from"]

        if datetime.strptime(date_from, '%Y-%m-%dT%H:%M:%S').date == today:
            continue

        location = date_range_fields["title"]

        if date_range_fields["stations"]:
            for station in date_range_fields["stations"]:
                for meal in station["meals"]:
                    if meal in jerk_chicken_dict:
                        chicken_days.append((location, meal))

    return list(set(chicken_days))

def tweet(message: str):
    auth = tweepy.OAuthHandler(keys.api_key, keys.api_secret)
    auth.set_access_token(keys.access_token, keys.access_token_secret)
    tweepy.API(auth).update_status(message)

def main():
    chicken_meals = get_chicken_meals()

    if len(chicken_meals) == 0:
        """
        No jerk chicken today
        """

        tweet('\N{white heavy check mark} No jerk chicken today')
    else:
        """
        Jerk chicken today!
        
         - ... at ...
         - ... at ...
         ...
        """

        msg = ["\N{Police Cars Revolving Light} Jerk chicken today!\n"]
        for m in chicken_meals:
            location = m[0]
            meal = m[1]

            for hall in ["JJs", "Chef Mike", "John Jay", "Ferris"]:
                if hall in location:
                    location = hall
                    break
            else:
                # no break
                location = "a dining hall"

            msg.append(f" - {jerk_chicken_dict[meal]} at {location}")

        tweet("\n".join(msg))

if __name__ == '__main__':
    main()
