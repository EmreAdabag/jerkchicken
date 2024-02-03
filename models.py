from dataclasses import dataclass

@dataclass(slots=True)
class Keyword:
    title: str
    nid: str
    type: str
    path: str

@dataclass(slots=True)
class JerkChickenMeal:
    meal_name: str
    meal_of_day: str  # Breakfast, Lunch, or Dinner
