import requests
import re

link = "https://dining.columbia.edu/content/spring-ferris-week-3-saturday-02-03-24"

def is_jerk_chicken(link):
    pattern = r'jerk ?chicken'
    response = requests.get(link)

    # text = "some sample text including different variations like JerkChicken, jerk chicken, JERK CHICKEN, etc."

    matches = re.findall(pattern, response.text, re.IGNORECASE)

    return len(matches) > 0