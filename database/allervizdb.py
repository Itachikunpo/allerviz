#%%
import pymongo
import json
import pandas as pd
from numpy import setdiff1d
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
                  f"Defaulting to example database file: {self.__example_dbfile}")
            example_collection = self.__DB["Example"]
            self.LoadData(path=self.__example_dbfile)
        else:
            try:
                print(f"Restarting database with Allerviz Scraped Data.")
                self.__InitRestaurantsCollection(data_path=Path(data_path).resolve())
            except FileNotFoundError:
                raise FileNotFoundError("Failed to import data from LoadData(). Check relative pathing.\n"
                                        f"\tGiven location not found: {data_path}\n"
                                        f"\tCurrent location: {Path.cwd()}\n\n")

        self.__loaded = True

    def __InitRestaurantsCollection(self, data_path=None):
        """InitMenuItemsCollection
        Create the Menu_Items collection and Load it into the mongodb instance
        Start off the InitRestaurantsCollection() as well
        """
        menu_items = self.__DB["Restaurants_Menus"]
        menu_items_df = self.LoadData(path=data_path, rtn_df=True, clean_menu_data=True, reorg_menu_to_restaurant=True)
        self.InsertData(collection_name="Restaurants_Menus", data=menu_items_df)
        self.__InitMenuItemsCollection(menu_items=menu_items_df)
        pass

    def __InitMenuItemsCollection(self, menu_items=None):
        restaurants = self.__DB["Menu_Items"]

        """Create the data
        """
        wrangled_data = menu_items
        # self.LoadData(collection_name="Restaurants_Menus", data=wrangled_data)
        pass

    def __CleanMenuData(self, menu_data):
        menu_data['cuisine'] = menu_data['cuisine'].astype('object').map(lambda cuisine: cuisine.strip("|").split("|"))
        return menu_data

    def __ReorgMenuDataToRestauranteData(self, menu_data):
        # group = df.groupby('restaurant_name')group.apply(lambda x: x['menu_items'].unique())
        return menu_data


    def LoadData(self, path=None, rtn_df=False, clean_menu_data=False, reorg_menu_to_restaurant=False):
        path = Path(path).resolve()
        print(f"Loading in data from file: \n\t{path}")
        df = pd.read_csv(path, encoding = "utf-8")

        if clean_menu_data:
            df = self.__CleanMenuData(menu_data=df)
        if reorg_menu_to_restaurant:
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
            print(f"New Data was inserted into MongoDB Server({self.__db_name}), in Collection: {collection_name} ")
        else:
            print(f"The Collection, {collection_name}, was already found in database")

    def GetMenuItemsDataFrame(self, optional_query={}):
        # Make a query to the specific DB and Collection
        return self.QueryToDataFrame(collectionName="Menu_Items", query=optional_query)

    def GetRestaurantsDataFrame(self, optional_query={}):
        # Make a query to the specific DB and Collection
        return self.QueryToDataFrame(collectionName="Restaurants_Menus", query=optional_query)

    def QueryToDataFrame(self, collectionName=None, query={}):
        # Make a query to the specific Collection
        if collectionName in self.GetCollectionNames():
            if query:
                data = self.__DB[collectionName].find(query)
            else:
                data = self.__DB[collectionName].find(query)
        else:  # Collection was not found
            data = None

        # Expand the cursor and construct the DataFrame
        return pd.DataFrame(list(data))

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
            return None

    def GetCollectionNames(self):
        return self.__DB.list_collection_names()

    def GetNamesOfRestaurants(self):
        if self.IsDBLoaded():
            return self.__DB["Menu_Items"].distinct("restaurant_name")
        else:
            return None

    def GetNumberOfRestaurants(self):
        return len(self.GetNamesOfRestaurants())

    def GetEstimatedDocumentCount(self, collection_name=None):
        if collection_name in self.GetCollectionNames():
            return self.__DB[collection_name].estimated_document_count()

    def DropDatabase(self, db_name=None):
        if db_name is None:
            db_del_list = setdiff1d(self.__client.database_names(), self.__base_dbs)
            for db in db_del_list:
                self.__client.drop_database(db)
        else:
            try:
                self.__client.drop_database(db_name)
            except Exception as e:
                print(e)
