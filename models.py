from dataclasses import dataclass

@dataclass(slots=True)
class Keyword:
    title: str
    nid: str
    type: str
    path: str

@dataclass(slots=True)
class Menu:
    dining_hall: str
    path: str

@dataclass(slots=True)
class JerkChickenMeal:
    food_names: [str]
    time_of_day: str

@dataclass(slots=True)
class JerkChickenEntry:
    dining_hall: str
    meals: list[JerkChickenMeal]
