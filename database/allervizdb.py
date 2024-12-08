#%%
import pymongo
import json
import pandas as pd
import numpy as np
import re
from random import sample
from pymongo import MongoClient
from pathlib import Path
from database.src.formulae4prediction import rcv, predict_single, predict_tuple, generall_prediction


base_allergens = ["Dairy","Egg","Fish","Shellfish","Tree nut","Peanut","Wheat","Soybean"]

milk=['buttermilk', 'cottage', 'cream', 'creamer', 'creamy', 'creme', 'ghee', 'half-and-half',
'milk', 'yogurt', 'bocconcini', 'mozzarella', 'gouda', 'swiss', 'brie', 'butter','cheese', 'custard', 'pudding',
'whey','Au gratin','bread','cookie','Cereals','Chewing gum','cracker','cake','Donuts',
'Margarine','Mashed potatoes','Nougat','Salad dressings','Sherbet',
'white sauces'
]

eggs=['egg','breaded','batter-fried', 'caesar', 'cream', 'puff','crepe','waffle','custard','pudding','ice cream', 'cappuccino',
      'candy', 'fizze','marshmallow', 'marzipan', 'mayonnaise', 'meatloaf', 'meatball','Meringue','frosting','pasta','soufflés']

fish = ['fish','albacore', 'bass', 'catfish', 'cod', 'fish', 'flounder', 'grouper', 'haddock', 'halibut', 'mahi',
		'monkfish', 'salmon', 'shark', 'snapper', 'sole', 'swordfishes', 'trouts', 'tuna', 'bluefish',
		'bonito', 'rockfish', 'mackerel', 'naruto', 'drum', 'marlin', 'tilapia', 'carp', 'kingfish',
		'mullet', 'whitefish', 'kipper', 'torsk', 'saltfish','Worcestershire']

shellfish=[
    'Cockle','Cuttlefish','Clam','Loco','Mussel',
    'Octopus','Oyster','Periwinkle','Scallop',
    'Squid','Nautilus',"crustacean","crab",
    "lobster", "sea snail",
]

tree_nuts=[
    'almond', 'butternut', 'candlenut', 'cashew',
    'chestnut', 'hazelnut', 'macadamia', 'nut',
	'pecan', 'pistachio', 'walnut','Brazil nut','Filbert'
]

peanuts=['peanut']

wheat=[
    'wheat','Bran', "bread", 'Bread crumb','Bulgur','Couscous',
    'Durum','Einkorn','Farina','Farro', 'emmer','Kamut',
    'Semolina','Sprouted wheat','Triticale',
    "rye", "sourdough", "tortilla", "soda bread", "flatabread",
    "crosissant", "bun", "bagel", "donut", 'cracker','cake',
    "cornbread", "waffle", "pancake", "muffin", "biscuit",
]

soybeans=[
    'Edamame','Miso','Natto','Soy','Tamari','Tempeh','Tofu'
]

allergen_map = [milk, eggs, fish, shellfish, tree_nuts, peanuts, wheat, soybeans]

class AllervizDB(object):
    def __init__(self, db_name=None):
        self.__db_name = db_name
        self.__client = MongoClient("localhost", 27017, maxPoolSize=50)
        self.__base_dbs = ['admin', 'config', 'local']
        self.__example_dbfile = Path("data/Portland-Grubhub-short.csv")
        self.__DB = self.__client[self.__db_name]
        self.__loaded = False
        self.TEST = None

        np.random.seed(42)

    def Load(self, data_path=None, example=False, override_load=False, checkdb_exists=False):
        # Drop all existing databases under this name and load the data
        if checkdb_exists:
            if "allerviz" in self.__client.list_database_names():
                print("\n\nDatabase found not going to drop!\n\n")
                self.__loaded = True
                return
            else:
                self.DropDatabase()

        if override_load:
            self.DropDatabase()

        # TODO Remove the example section its just for testing
        if example:
            print("Restarting database with example data.\n"
                  f"Defaulting to example database file: '{self.__example_dbfile}''")
            example_collection = self.__DB["Example"]
            self.LoadData(path=self.__example_dbfile)
        else:
            print(self.__loaded)
            print(override_load)
            if self.__loaded and not override_load:
                print("Data is already loaded.\n"
                      "If you still want to load in the data set override_load=True.")
            else:
                try:
                    print(f"Restarting database with Allerviz Scraped Data.")
                    self.__InitRestaurantsCollection(data_path=Path(data_path).resolve())
                except FileNotFoundError:
                    raise FileNotFoundError("Failed to import data from LoadData(). Check relative pathing.\n"
                                            f"\tGiven location not found: '{data_path}'\n"
                                            f"\tCurrent location: '{Path.cwd()}'\n\n")
        self.__loaded = True

    def __InitRestaurantsCollection(self, data_path=None):
        """InitMenuItemsCollection
        Create the Menu_Items collection and Load it into the mongodb instance
        Start off the InitRestaurantsCollection() as well
        """
        menu_items = self.__DB["Restaurants_Menus"]
        menu_items_df = self.LoadData(path=data_path,
                                      rtn_df=True,
                                      clean_menu_data=True,
                                      reorg_menu_to_restaurant=True,
                                      init_allergy_scores=True)
        self.InsertData(collection_name="Restaurants_Menus", data=menu_items_df)
        # self.__InitMenuItemsCollection(menu_items=menu_items_df)

    def __InitMenuItemsCollection(self, menu_items=None):
        restaurants = self.__DB["Menu_Items"]
        wrangled_data = menu_items
        # self.LoadData(collection_name="Restaurants_Menus", data=wrangled_data)
        raise NotImplementedError

    def __CleanMenuData(self, menu_data):
        menu_data = menu_data.rename(columns={"menu_item":"item", "restaurant_name":"restaurant"}, errors="raise")
        menu_data['cuisine'] = menu_data['cuisine'].astype('object').map(lambda cuisine: cuisine.strip("|").split("|"))
        return menu_data

    def __ReorgMenuDataToRestauranteData(self, menu_data):

        # Drop menu items and their description to get the top level data of the restaurant
        menu_filtered = menu_data.drop(['item', 'description', "transformed_desc", "street", "city", "state", "zip", "latitude", "longitude"], axis = 1)
        menu_filtered = menu_filtered.drop_duplicates(subset="restaurant")

        # Initialize new dataframe for grouped menu items
        restaurant_menu_items = pd.DataFrame()
        restaurant_menu_items["menu"] = np.nan
        restaurant_menu_items["menu"] = restaurant_menu_items["menu"].astype("object")
        # Start another DF by grouping on the restaurant name
        menu_grouped = menu_data.groupby("restaurant")
        city_n_states = menu_grouped['city','state'].apply(lambda x: list(np.unique(x))).to_frame()
        city_n_states = city_n_states.rename(columns={0:"state&city"}).reset_index()

        # Iterate over the groups
        for idx, grp in enumerate(menu_grouped.groups):
            # grab the menu items per restaurant and recordize it to prep for insertion into DB
            menu_items = menu_grouped.get_group(grp)[["item", "description", "transformed_desc"]].to_dict("records")

            # Add to the DF the restaurant name and the list of menu items
            restaurant_menu_items.loc[idx, ["restaurant", "menu"]] = grp, menu_items

        # Join the dataframes on the restaurant names to add the menu items to the correct restaurant
        reorged_menu_to_restaurants = menu_filtered.join(restaurant_menu_items.set_index('restaurant'), on='restaurant')
        reorged_menu_to_restaurants = reorged_menu_to_restaurants.join(city_n_states.set_index('restaurant'), on='restaurant')

        return reorged_menu_to_restaurants

    def __InitMenuAllergyScores(self, restaurant_data=None):
        if restaurant_data is not None:
            restaurant_data['menu'] = restaurant_data.apply(lambda x: self.__AddMenuItemAllergenLabels(menu=x['menu']), axis=1)
            restaurant_data['allergens'] = restaurant_data.apply(lambda x: self.__GenerateRestaurantAllergenLabels(menu_data=x['menu']), axis=1)
            restaurant_data['menu'] = restaurant_data.apply(lambda x: self.__CalculateMenuItemAllergyScores(menu=x['menu']), axis=1)
            return restaurant_data
        else:
            raise AttributeError("No restaurant_data recieved in AllervizDB().__InitMenuAllergyScores()")

    def __AddMenuItemAllergenLabels(self, menu=None):

        if isinstance(menu, dict):
            menu["allergens"] = self.__GenerateMenuItemAllergenLabels(item=menu["item"], description=menu["description"])
        else:
            for item in menu:
                item["allergens"] = self.__GenerateMenuItemAllergenLabels(item=item["item"], description=item["description"])
        return menu

    def __GenerateMenuItemAllergenLabels(self, item=None, description=None):
        allergens_array_per_item = list()

        # convert some bad data to empty out np.nans
        if isinstance(item, float):
            item = ""
        if isinstance(description, float):
            description = ""

        full_search_string = item + " " + description
        for allergens in allergen_map:
            allergens_array_per_item.append(self.__lookup(search_str=full_search_string, search_list='|'.join(allergens)))

        allergen_labels = self.ConvertAllergenArrayToLabels(allergens_array=allergens_array_per_item)
        return allergen_labels

        # weight chance to have no allergens
        if np.random.choice(np.arange(0, 2), p=[0.40, 0.60]):
            allergens = list(sample(base_allergens, k=np.random.randint(0, len(base_allergens))))
        else:
            allergens = list()
        return allergens

    def __GenerateRestaurantAllergenLabels(self, menu_data=None):
        restaurant_allergens_unique = set()
        for food in menu_data:
            allergens_array_per_item = list()
            if isinstance(food["item"], float):
                food["item"] = ""
            if isinstance(food["description"], float):
                food["description"] = ""
            full_search_string = food["item"] + " " + food["description"]
            for allergens in allergen_map:
                allergens_array_per_item.append(self.__lookup(search_str=full_search_string, search_list='|'.join(allergens)))

            allergen_labels = self.ConvertAllergenArrayToLabels(allergens_array=allergens_array_per_item)
            restaurant_allergens_unique.update(allergen_labels)
        return list(restaurant_allergens_unique)

    def __lookup(self, search_str=None, search_list=None):
            search_obj = re.search(search_list.lower(), str(search_str).lower())
            if search_obj :
                return 1
            else:
                return 0

    def ConvertAllergenLabelsToArray(self, allergen_labels=None):
        return [1 if x in allergen_labels else 0 for i,x in enumerate(base_allergens)]

    def ConvertAllergenArrayToLabels(self, allergens_array=None):
        return [base_allergens[i] for i,x in enumerate(allergens_array) if x]


    def __CalculateMenuItemAllergyScores(self, menu=None, item=None, description=None):
        # TODO Figure out if we are getting a menu<List of dicts> or a single item and description
        for item in menu:
            item["allergy_score"] = np.round(np.random.uniform(0,100), 2)
        return menu

    def __CalculateRestaurantAllergyScores(self, restaurant_data=None):
        restaurant_data["total_allergy_score"] = restaurant_data.apply(lambda x: np.round(np.random.uniform(0,100), 2), axis = 1)
        return restaurant_data

    def LoadData(self, path=None, rtn_df=False, **kwargs):
        path = Path(path).resolve()
        print(f"Loading in data from file: \n\t'{path}'")
        df = pd.read_csv(path, encoding = "utf-8")

        # print(df.info())
        # print(df.dtypes)

        if kwargs.get("clean_menu_data", False) == True:
            df = self.__CleanMenuData(menu_data=df)
        if kwargs.get("reorg_menu_to_restaurant", False)  == True:
            df = self.__ReorgMenuDataToRestauranteData(menu_data=df)
        if kwargs.get("init_allergy_scores", False)  == True:
            df = self.__InitMenuAllergyScores(restaurant_data=df)
            df = self.__CalculateRestaurantAllergyScores(restaurant_data=df)
        if kwargs.get("clean_df_before_insert", False) == True:
            # df = df.drop([""])
            # menu_filtered = menu_data.drop(['item', 'description', "transformed_desc", "street", "city", "state", "zip", "latitude", "longitude"], axis = 1)
            pass

        if rtn_df:
            return df
        else:
            return df.to_dict('records')


    def InsertData(self, collection_name=None, data=None, ignore_type=None):
        if collection_name not in self.GetCollectionNames():
            print(f"Attempting to insert entries into Collection: {collection_name}")
            if not ignore_type:
                if isinstance(data, list) and all((isinstance(x, dict) for x in data)):
                    # simple check that it is a list of dictionaries or a list of records
                    loaded_data = data
                elif isinstance(data, pd.DataFrame):
                    loaded_data = data.to_dict('records')
                else:
                    raise AttributeError(f"Incompatible data type: ({type(data)}). Only pandas.DataFrame or dict objects allowed to insert into Database")
            else:
                loaded_data = data

            self.__DB[collection_name].insert_many(loaded_data, ordered=False)
            print(f"New Data inserted into MongoDB Server({self.__db_name}), Collection: '{collection_name}'")
        else:
            print(f"The Collection, '{collection_name}'', was already found in database")

    def QueryMenuItems(self, query={}, limit=None, rtn_df=False):
        # Make a query to the specific DB and Collection
        return self.QueryToDB(collection_name="Menu_Items", query=query, limit=limit, rtn_df=False)

    def QueryRestaurants(self, query={}, limit=None, rtn_df=False):
        # Make a query to the specific DB and Collection
        return self.QueryToDB(collection_name="Restaurants_Menus", query=query, limit=limit, rtn_df=False)

    def QueryToDB(self, collection_name=None, query={}, limit=None, rtn_df=False):
        # Make a query to the specific Collection
        if collection_name in self.GetCollectionNames():
            if query and limit:
                data = self.__DB[collection_name].find(query, limit=limit)
            elif limit:
                data = self.__DB[collection_name].find(limit=limit)
            else:
                data = self.__DB[collection_name].find(query)
        else:  # Collection was not found
            data = None

        # Expand the cursor and construct the DataFrame
        if rtn_df:
            return pd.DataFrame(list(data))
        else:
            return data

    def IsDBLoaded(self):
        return self.__loaded

    def GetDatabaseName(self):
        return self.__DB

    def GetMongoClient(self):
        return self.__client

    def GetMongoDB(self):
        return self.__DB

    def GetCollection(self, collection_name):
        if collection_name in self.GetCollectionNames():
            return self.__DB[collection_name]
        else:
            raise AttributeError(f"No Collection found with name: '{collection_name}'")

    def GetRestaurantCollection(self):
        if "Restaurants_Menus" in self.GetCollectionNames():
            return self.__DB["Restaurants_Menus"]
        else:
            raise AttributeError(f"No Collection found with name: 'Restaurants_Menus'")

    def GetCollectionNames(self):
        return self.__DB.list_collection_names()

    def GetNamesOfRestaurants(self):
        if self.IsDBLoaded():
            return self.__DB["Restaurants_Menus"].distinct("restaurant")
        else:
            return None

    def GetRestaurantsMenu(self, restaurant=None, rtn_df=False):
        data = None
        if isinstance(restaurant, list):
            data = self.QueryRestaurants(query={ "restaurant": { "$in": restaurant } }, rtn_df=rtn_df)
            if not rtn_df:
                data =  [restaurant["menu"] for restaurant in data]
        elif isinstance(restaurant, str):
            data = self.QueryRestaurants(query={"restaurant": restaurant}, rtn_df=rtn_df)
            if not rtn_df:
                data = next(data)["menu"]
        else:
            raise AttributeError("No restaurant name given!! Unable to query.")

        return data

    def GetRestaurantsInfo(self, restaurant=None, rtn_df=False, all=False):
        data = None
        if all:
            data = self.QueryRestaurants(rtn_df=rtn_df)
            if not rtn_df:
                data = list(data)
        elif isinstance(restaurant, list):
            data = self.QueryRestaurants(query={ "restaurant": { "$in": restaurant } }, rtn_df=rtn_df)
            if not rtn_df:
                data = list(data)
        elif isinstance(restaurant, str):
            data = self.QueryRestaurants(query={"restaurant": restaurant}, rtn_df=rtn_df)
            if not rtn_df:
                data = next(data)
        else:
            raise AttributeError("No restaurant name given!! Unable to query.")

        return data

    def GetNumberOfRestaurants(self):
        return len(self.GetNamesOfRestaurants())

    def GetEstimatedDocumentCount(self, collection_name=None):
        if collection_name in self.GetCollectionNames():
            return self.__DB[collection_name].estimated_document_count()

    def DropDatabase(self, db_name=None):
        print(f"\n\nDatabase going to be dropped: {db_name}!\n\n")
        if db_name is None:
            db_del_list = np.setdiff1d(self.__client.list_database_names(), self.__base_dbs)
            for db in db_del_list:
                self.__client.drop_database(db)
        else:
            try:
                self.__client.drop_database(db_name)
            except Exception as e:
                print(e)

# %%
if __name__ == "__main__":
    import pdb

    print("database")
    # path = "data/Portland-Grubhub-short.csv"



    path = "data/Grubhub-final.csv"
    path = "data/Grubhub-final-short.csv"
    mongodb = AllervizDB(db_name='allerviz')
    mongodb.Load(Path(path).resolve())


    # shortmenu = mongodb.LoadData(path="data/Portland-Grubhub-short.csv", rtn_df=True)
    # mediummenu = mongodb.LoadData(path="data/Portland-Honolulu-San_Diego-Grubhub.csv", rtn_df=True)
    # fullmenu = mongodb.LoadData(path="data/Grubhub.csv", rtn_df=True)

# %%
if __name__ == "__main__":
    # id              INTEGER PRIMARY KEY AUTOINCREMENT,
    # item_id         INTEGER,
    # restaurant      TEXT,
    # menu_item       TEXT,
    # description     TEXT,
    # allergen        TEXT,
    # allergy_score   REAL,
    from bson.objectid import ObjectId
    from pprint import pprint
    restaurant_extract = ["restaurant", "allergens", "cuisine", "total_allergy_score", "city&State"]
    menu_extract = ["menu"]
    # t = next(mongodb.QueryRestaurants(query={"_id":ObjectId("5fbb2f0ed6aec6a5237271af")}))
    t = next(mongodb.GetRestaurantCollection().find(limit=1))

    restaurant_info = {key: t[key] for key in restaurant_extract}
    pprint(restaurant_info)
    menu = t["menu"]
    print(len(menu))





# %%
