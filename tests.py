from jerkchickenchecker import *
import datetime
import json


def test_get_chicken_dict():    
    chicken_dict = get_chicken_dict()
    try:
        assert len(chicken_dict) > 0, f"Error fetching chicken dict, returned length 0"

        print("passed get_chicken_dict test")
        return True

    except Exception as e:
        log_error(e)
        return False



def test_get_chicken_meals():
    with open('sample_chicken_dict.json', 'r') as fp:
        chicken_dict = json.load(fp)
    with open('sample_menus.json', 'r') as fp:
        menus_dict = json.load(fp)
    date = datetime.date(2023, 2, 5)

    chicken_days = get_chicken_meals(chicken_dict, menus_dict, date)

    try:
        assert chicken_days == [('JJs Week 3_Sunday_Lunch & Dinner_02-05-2023', '3585')],\
            f"get_chicken_meals returned unexpected value: {chicken_days}"

        print("passed get_chicken_meals test")
        return True

    except Exception as e:
        log_error(e)
        return False




def test_get_chicken_message():
    with open('sample_chicken_dict.json', 'r') as fp:
        chicken_dict = json.load(fp)
    with open('sample_chicken_meals.json', 'r') as fp:
        chicken_meals = json.load(fp)

    msg = get_chicken_message(chicken_dict, chicken_meals)

    try:
        assert msg == ['🚨 Jerk chicken today!\n', " - JJ's Jerk Chicken Quesadilla with Tamarind Sauce at JJs"],\
            f"get_chicken_message returned unexpected value: {msg}"
        
        print("passed get_chicken_message test")
        return True

    except Exception as e:
        log_error(e)
        return False




def test_all():
    return all([
        test_get_chicken_dict(),
        test_get_chicken_meals(),
        test_get_chicken_message()
    ])




if __name__ == '__main__':
    test_all()