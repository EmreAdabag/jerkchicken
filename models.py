from dataclasses import dataclass

@dataclass(slots=True)
class Keyword:
    title: str
    nid: str
    type: str
    path: str

@dataclass(slots=True)
class JerkChickenMeal:
    food_name: str
    is_name: bool

    def __post_init__(self):
        self.food_name = self.food_name.strip()
        # self.food_name = self.food_name if is_name else self.food_name + " (contains jerk chicken)"

@dataclass(slots=True)
class Setting:
    dining_hall: str
    meal_of_day: str

    def __post_init__(self):
        self.meal_of_day = self.meal_of_day.strip().lower()

@dataclass(slots=True)
class JerkChickenEntry:
    meals: list[JerkChickenMeal]
    setting: Setting
