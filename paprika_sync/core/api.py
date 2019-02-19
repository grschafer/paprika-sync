import requests


# Paprika API docs: https://gist.github.com/mattdsteele/7386ec363badfdeaad05a418b9a1f30a
RECIPES_URL = 'https://www.paprikaapp.com/api/v1/sync/recipes/'
RECIPE_URL = 'https://www.paprikaapp.com/api/v1/sync/recipe/{uid}/'


def get_recipes(paprika_account):
    resp = requests.get(RECIPES_URL, auth=(paprika_account.username, paprika_account.password))
    return resp.json()['result']


def get_recipe(uid, paprika_account):
    url = RECIPE_URL.format(uid=uid)
    resp = requests.get(url, auth=(paprika_account.username, paprika_account.password))
    return resp.json()['result']
