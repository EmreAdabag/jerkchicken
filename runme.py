from jerkchickenchecker import *
from tests import test_all


def main():

    if not test_all():
        log_error("unit tests didn't pass, not tweeting")
        return
    
    jerk_chicken_dict = get_chicken_dict()
    menus = get_menus()

    chicken_meals = get_chicken_meals(jerk_chicken_dict, menus, datetime.today().date())
    
    msg = get_chicken_message(jerk_chicken_dict, chicken_meals)

    tweet("\n".join(msg))


if __name__ == '__main__':
    main()
