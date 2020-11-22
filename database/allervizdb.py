#%%
import pymongo
import json
import pandas as pd
import numpy as np
from pymongo import MongoClient
from pathlib2 import Path

class AllervizDB(object):
    def __init__(self, db_name=None):
        self.__db_name = db_name
        self.__client = MongoClient("localhost", 27017, maxPoolSize=50)
        self.__base_dbs = ['admin', 'config', 'local']
        self.__example_dbfile = Path("data/Portland-Grubhub-short.csv")
        self.__DB = self.__client[self.__db_name]
        self.__loaded = False

    def Load(self, data_path=None, example=False):
        # Drop all existing databases under this name and load the data
        self.DropDatabase()

        # TODO Remove the example section its just for testing
        if example:
            print("Restarting database with example data.\n"
                  f"Defaulting to example database file: '{self.__example_dbfile}''")
            example_collection = self.__DB["Example"]
            self.LoadData(path=self.__example_dbfile)
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
        menu_items_df = self.LoadData(path=data_path, rtn_df=True, clean_menu_data=True, reorg_menu_to_restaurant=True)
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
        menu_filtered = menu_data.drop(['item', 'description'], axis = 1)
        menu_filtered = menu_filtered.drop_duplicates(subset="restaurant")

        # Initialize new dataframe for grouped menu items
        restaurant_menu_items = pd.DataFrame()
        # Start another DF by grouping on the restaurant name
        menu_grouped = menu_data.groupby("restaurant")
        # menu_grouped = menu_data.groupby("restaurant")['street','city', "state", "zip", "latitude", "longitude"].agg(["unique"])
        # menu_grouped = menu_data.groupby("restaurant")['street','city', "state", "zip", "latitude", "longitude"].apply(lambda x: list(np.unique(x)))

        # Iterate over the groups
        for idx, grp in enumerate(menu_grouped.groups):
            # grab the menu items per restaurant and recordize it to prep for insertion into DB
            menu_items = menu_grouped.get_group(grp)[["item", "description"]].to_dict("records")

            # Add to the DF the restaurant name and the list of menu items
            restaurant_menu_items.loc[idx, ["restaurant", "menu"]] = grp, menu_items

        # Join the dataframes on the restaurant names to add the menu items to the correct restaurant
        reorged_menu_to_restaurants = menu_filtered.join(restaurant_menu_items.set_index('restaurant'), on='restaurant')

        return reorged_menu_to_restaurants

    def __CalculateMenuAllergyScores():
        pass

    def __CalculateRestaurantAllergyScores():
        pass

    def LoadData(self, path=None, rtn_df=False, **kwargs):
        path = Path(path).resolve()
        print(f"Loading in data from file: \n\t'{path}'")
        df = pd.read_csv(path, encoding = "utf-8")

        if kwargs["clean_menu_data"] == True:
            df = self.__CleanMenuData(menu_data=df)
        if kwargs["reorg_menu_to_restaurant"] == True:
            df = self.__ReorgMenuDataToRestauranteData(menu_data=df)

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

    def GetRestaurantsInfo(self, restaurant=None, rtn_df=False):
        data = None
        if isinstance(restaurant, list):
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
    print(Path.cwd())
    if str(Path.cwd()) != __file__:
        path = "database/data/Portland-Honolulu-San_Diego-Grubhub.csv"
    else:
        path = "data/Portland-Honolulu-San_Diego-Grubhub.csv"

    mongodb = AllervizDB(db_name='allerviz')
    mongodb.Load(Path(path).resolve())
    menu = mongodb.GetRestaurantsMenu("Krispy Rice")
