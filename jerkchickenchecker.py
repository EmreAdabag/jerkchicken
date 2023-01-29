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

menu_url = "https://dining.columbia.edu/cu_dining/rest/menus/nested"


def getchickenlist():
    
    chicken_days = []
    today = datetime.today().date

    menus_json = requests.get(menu_url).json()

    for menu in menus_json:
    
        date_range_fields = menu["date_range_fields"][0]
        date_from = date_range_fields["date_from"]

        if datetime.strptime(date_from, '%Y-%m-%dT%H:%M:%S').date == today:
            continue
            
        location = date_range_fields["title"]

        if date_range_fields["stations"]:
            for station in date_range_fields["stations"]:
                for meal in station["meals"]:
                    if int(meal) in jerk_chicken_dict:
                        chicken_days.append((location, int(meal)))
        

    return list(set(chicken_days))


def tweet(message: str):
    auth = tweepy.OAuthHandler(keys.api_key, keys.api_secret)
    auth.set_access_token(keys.access_token, keys.access_token_secret)
    tweepy.API(auth).update_status(message)


if __name__ == '__main__':
    
    chickenlist = getchickenlist()
    msg = ''

    if len(chickenlist) == 0:
        msg += '\N{white heavy check mark} no jerk chicken today'
    else:
        for i, m in enumerate(chickenlist):
            location = m[0]
            meal = m[1]

            if "JJs" in location:
                location = "JJs"
            elif "Chef Mike" in location:
                location = "Chef Mike"
            elif "John Jay" in location:
                location = "John Jay"
            elif "Ferris" in location:
                location = "Ferris"

            if location in {"JJs", "Chef Mike", "John Jay", "Ferris"}:
                msg += "{} at {} today{}".format(jerk_chicken_dict[meal], location, "" if i == len(chickenlist)-1 else "\n")

    tweet(msg)