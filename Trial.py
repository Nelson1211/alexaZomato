from flask import Flask
from flask_ask import Ask, statement, question, session, convert_errors
from zomato import Zomato
import json
from unidecode import unidecode
import re

app = Flask(__name__)
ask = Ask(app, "/zomato")
z = Zomato("309e354eabc5cf4d7ea8eddef054c677")

id=0
restaurant_names=[]
details = []
cuisine = []
cost = []
rating = []
full_address = []
count = 0
global noloc
noloc = 0
address = []
detail_dict = {}
cuisine_dict = {}
cost_dict = {}
rating_dict = {}
full = {}
res_name = ""
budget = 0
currency = ""

def get_categories():
    data=z.parse("categories","")
    print data
    data_json= json.loads(data)
    l=[]
    for x in data_json['categories']:
        l.append(unidecode(x[u'categories'][u'name'])+"....")
    l=' '.join([i for i in l])
    l = l.replace('&','and')
    return l

def get_name(res):
    data=z.parse("search","q={}".format(res))
    #print data
    data= json.loads(data)
    global restaurant_names 
    global details
    global cuisine
    global cost 
    global count
    global detail_dict
    global cuisine_dict
    global cost_dict
    global rating_dict
    global currency
    global full_address
    global full
    restaurant_names = []
    details = []
    cuisine = []
    cost = []
    count = data["results_shown"]
    if count == 0:
        return "I could not find any outlets around."
    for i in range(count):
        if data["restaurants"][i]["restaurant"]["name"]:
            if unidecode(data["restaurants"][i]["restaurant"]["name"]).lower() == res.lower():
                restaurant_names.append(unidecode(data["restaurants"][i]["restaurant"]["name"]).lower())
                details.append(unidecode(data["restaurants"][i]["restaurant"]["location"]["locality"]))
                full_address.append(unidecode(data["restaurants"][i]["restaurant"]["location"]["address"]).replace('&','and'))
                cuisine.append(unidecode(data["restaurants"][i]["restaurant"]["cuisines"]))
                cost.append(data["restaurants"][i]["restaurant"]["average_cost_for_two"])
                rt =str(data["restaurants"][i]["restaurant"]["user_rating"]["aggregate_rating"]).replace('.',' point ')
                rating.append(rt)
    r=' '.join([i.replace('&','and')+"...." for i in restaurant_names])
    currency = data["restaurants"][0]["restaurant"]["currency"]
    detail_dict = {}
    cuisine_dict = {}
    cost_dict = {}
    rating_dict = {}
    full = {}
    for i in range(len(restaurant_names)):
        detail_dict[details[i]]=details[i]
        cuisine_dict[details[i]]=cuisine[i]
        cost_dict[details[i]]=cost[i]
        rating_dict[details[i]]=rating[i]
        full[details[i]] = full_address[i]
    return r

def get_collections(cid):
    data=z.parse("collections","city_id={}".format(cid))
    print data
    data_json= json.loads(data)
    l=[]
    for x in data_json['collections']:
        l.append(unidecode(x[u'collection'][u'title'])+"....")
    l=' '.join([i for i in l])
    l = l.replace('&amp;','')
    l = l.replace('caf&eacute;s','cafe')
    l = l.replace('&#039;','')
    return l

def get_restaurant(id,type):
    data = z.parse("location_details","entity_id={}".format(id)+","+"entity_type={}".format(type))
    data=json.loads(data)

    global restaurant_names 
    global details
    global cuisine
    global cost 
    global detail_dict
    global cuisine_dict
    global cost_dict
    global rating_dict
    global currency
    con = 0
    restaurant_names = []
    details = []
    cuisine = []
    cost = []
    for i in range(10):
        if data["best_rated_restaurant"][i]["restaurant"]["name"]:
            if budget == 0:
                restaurant_names.append(unidecode(data["best_rated_restaurant"][i]["restaurant"]["name"]).lower())
                details.append(unidecode(data["best_rated_restaurant"][i]["restaurant"]["location"]["address"]).replace('&','and'))
                cuisine.append(unidecode(data["best_rated_restaurant"][i]["restaurant"]["cuisines"]))
                cost.append(data["best_rated_restaurant"][i]["restaurant"]["average_cost_for_two"])
                rt =str(data["best_rated_restaurant"][i]["restaurant"]["user_rating"]["aggregate_rating"]).replace('.',' point ')
                rating.append(rt)
            else:
                if int(data["best_rated_restaurant"][i]["restaurant"]["average_cost_for_two"]) <= budget:
                    restaurant_names.append(unidecode(data["best_rated_restaurant"][i]["restaurant"]["name"]).lower())
                    details.append(unidecode(data["best_rated_restaurant"][i]["restaurant"]["location"]["address"]).replace('&','and'))
                    cuisine.append(unidecode(data["best_rated_restaurant"][i]["restaurant"]["cuisines"]))
                    cost.append(data["best_rated_restaurant"][i]["restaurant"]["average_cost_for_two"])
                    rt =str(data["best_rated_restaurant"][i]["restaurant"]["user_rating"]["aggregate_rating"]).replace('.',' point ')
                    rating.append(rt)
    r=' '.join([i.replace('&','and')+"...." for i in restaurant_names])
    currency = data["best_rated_restaurant"][0]["restaurant"]["currency"]
    detail_dict = {}
    cuisine_dict = {}
    cost_dict = {}
    rating_dict = {}
    for i in range(len(restaurant_names)):
        detail_dict[restaurant_names[i]]=details[i]
        cuisine_dict[restaurant_names[i]]=cuisine[i]
        cost_dict[restaurant_names[i]]=cost[i]
        rating_dict[restaurant_names[i]]=rating[i]
    return r

def get_locationdetails(loc):
    data=z.parse("locations","query={}".format(loc))
    print data
    data_json= json.loads(data)
    if data_json["location_suggestions"] == []:
        print loc
        return "I have no information about such a location"
    l=[]
    for x in data_json["location_suggestions"]:
        global id 
        id = x[u'entity_id']
        type = x[u'entity_type']
    print type
    print "entity_id={}".format(id)
    s= get_restaurant(id,type)
    return s

@app.route('/')
def homepage():
    return "hi there, how ya doin?"

@ask.launch
def start_skill():
    welcome_message = 'Hello there, How may I assist you?'
    return question(welcome_message)

@ask.intent("AMAZON.YesIntent")
def share_headlines():
    s = get_categories()
    message = "The available categories are {}".format(s)
    return statement(message)

@ask.intent("WhereIntent")
def askLocation():
    q = "What is your location?"
    return question(q)

@ask.intent("LocationIntent")
def get_Location(Location):
    global address
    global noloc
    global currency
    address = [a.lower() for a in address]
    if noloc == 0:
        loc = get_locationdetails(Location)
        if loc == "I have no information about such a location":
            return statement("I have no information about such a location")
        return question("The restaurants around you are {}".format(loc)+". Which one would you like to know about?")
    else:
        j = 0
        for i in range(count):
            if Location == address[i]:
                j = i
                break
        noloc = 0
        return statement("It is rated {}".format(rating_dict[details[j]])+" by users  and is located at {}".format(full[details[j]])+"..... It serves {}".format(cuisine_dict[details[j]])+"... and the average cost for two people is {}".format(cost_dict[details[j]])+" {}".format(currency))

@ask.intent("CollectionIntent")
def share_collections():
    s = get_collections(id)
    message = "{}".format(s)
    return statement(message)

@ask.intent("CostIntent", convert={'Amount':int})
def share_cost(Amount):
    global budget
    budget = Amount
    q = "What is your location?"
    return question(q)


'''@ask.intent("CategoryIntent")
def share_categories():
    s = get_categories()
    message = "The available categories are {}".format(s)
    return statement(message)'''

@ask.intent("RestaurantIntent")
def share_detail_restaurants(Restaurant):
    global noloc
    global address
    global res_name
    global id
    global currency
    res_name = Restaurant.lower()
    trk = 0
    if id == 0:
        noloc = 1
        s = get_name(Restaurant)
        address = []
        for i in range(len(restaurant_names)):
            address.append(re.sub(r".*?, ","", details[i]))
        if s == "I could not find any outlets around.":
            return statement("{}".format(s))
        return question("There are {}".format(len(restaurant_names))+" outlets located in {}".format(address)+"..... Which one would you like to know about?")
    else:
        noloc = 0
        print restaurant_names
        for i in range(len(restaurant_names)):
            if res_name == restaurant_names[i]:
                trk = 1
                break
        if trk == 0:
            return statement("The mentioned Restaurant was not on the list.")
        id = 0
        return statement("It is rated {}".format(rating_dict[unidecode(Restaurant.lower())])+" by users  and is located at {}".format(detail_dict[unidecode(Restaurant.lower())])+"..... It serves {}".format(cuisine_dict[unidecode(Restaurant.lower())])+"... and the average cost for two people is {}".format(cost_dict[unidecode(Restaurant.lower())])+" {}".format(currency))



@ask.intent("AMAZON.HelpIntent")
def help_intent():
    return statement("You can ask me the following things... Restaurants near me... Restaurants within a budget of 50")

if __name__ == '__main__':
    app.run(debug=True)
