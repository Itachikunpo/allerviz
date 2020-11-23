#%%
from allervizdb import AllervizDB
from pathlib2 import Path

mongodb = AllervizDB(db_name='allerviz')
mongodb.Load(Path("data/Portland-Honolulu-San_Diego-Grubhub.csv").resolve())
df = mongodb.GetRestaurantsDataFrame()

#%%
print(len(df.to_dict('records')))
df[" restaurant"].unique()

#%%
df = pd.DataFrame({'restaurant':['Krispy Rice', 'Krispy Rice', 'Mumbo Gumbo', 'Mumbo Gumbo','Mumbo Gumbo',], 'menu_items':['The Box', 'Krispy Heaven', "Shrimp 'n Grits", "Red Beans N' Rice", "Boudin Sausage"]})
# print(df.head())
group = df.groupby('restaurant')
# print(group.head())
df2 = group.apply(lambda x: x['menu_items'].unique())
# print(df2.head())

# print(df[" restaurant"].unique())


test = [{"id":1,
        " restaurant":"Krispy Rice",
        "street":"1130 SW 17th Ave",
        "city":"Portland",
        "state":"OR",
        "zip":"97205" ,
        "latitude":45.518436,
        "longitude":-122.690475 ,
        "cuisine":["Asian", "Japanese"],
        "menu":[{"item":"The Box",
                    "description":"Edamame, The Original Spicy Tuna Krispy Rice"
                },
                {"item":"Krispy Heaven",
                    "description":"breaded chicken with some rice"
                },
            ]
        },
        {"id":2,
        " restaurant":"Mumbo Gumbo",
        "street":"6200 SE Milwaukie Ave",
        "city":"Portland",
        "state":"OR",
        "zip":"97202",
        "latitude":45.477779,
        "longitude":-122.64888,
        "cuisine":["American, Southern"],
        "menu":[{"item":"Gumbo(build your own)",
                "description":"Savory house-made sauce using fresh ingredient..."
                },
                {"item":"Red Beans N' Rice",
                "description":"Some rice with beans and sausage"
                },
            ]
        }
]

mongodb.InsertData(collection_name="test_nested",data=test)

#%%
df = mongodb.LoadData(path="data/Portland-Honolulu-San_Diego-Grubhub.csv", rtn_df=True, clean_menu_data=True)
df_filtered = df.drop(['_id', 'menu_item', 'description'], axis = 1)
df_filtered = df_filtered.drop_duplicates(subset=" restaurant")
# print(df.head())

df_filtered["menu"] = df_filtered["menu"].astype("object")
print(len(df_filtered))
y = 0
for i, x in enumerate(df_filtered[" restaurant"]):
    df2 = df[(df[" restaurant"] == x)]
    df_filtered.loc[df_filtered[" restaurant"] == x, "menu"] = df2
    y+=1
    if y==3:
        break
print(len(df2))
df_filtered.head()
df2

dict(tuple(df.groupby('restaurant')))
test = df.groupby("restaurant")
df_t = pd.DataFrame()
(df_t.loc[i,["restaurant", "menu"]] = x, test.get_group(x)[[ "item", "description"]].to_dict("records")
            for i, x in enumerate(test.groups))

#%%
df = mongodb.LoadData(path="data/Portland-Honolulu-San_Diego-Grubhub.csv",
                        rtn_df=True,
                        clean_menu_data=True)
df_filtered = df.drop(['item', 'description'], axis = 1)
df_filtered = df_filtered.drop_duplicates(subset="restaurant")
# print(type(df_filtered))
test = df.groupby("restaurant")
t = list()
df_t = pd.DataFrame()
for i,g in enumerate(test.groups):
    # if i == 3:
    #     break
    tmp = test.get_group(g)[["item", "description"]].to_dict("records")
    df_t.loc[i,["restaurant", "menu"]] = g, tmp
    t.append(tmp)
    # print(df_filtered.loc[df_filtered[' restaurant'] == g, 'menu'])
    # print(type(tmp))
    # df_filtered.loc[(df_filtered[' restaurant'] == g), ['menu']] = tmp
    # if isinstance(tmp, pd.core.frame.DataFrame):
    #     # print(f"{i}: {g} -> {tmp}")
    #     pass
    # else:
    #     print(f"{i}:None")

# test = df.groupby("restaurant")
# df_tt = pd.DataFrame()
# (df_tt.loc[i,["restaurant", "menu"]] = x, test.get_group(x)[[ "item", "description"]].to_dict("records")
#           for i, x in enumerate(test.groups))

dd = df_filtered.join(df_t.set_index('restaurant'), on='restaurant')

#%%
df = pd.read_csv("data/Portland-Honolulu-San_Diego-Grubhub.csv", encoding = "ISO-8859-1")

# print(f"Collections in DB: {mongodb.GetCollectionNames()}")
# print(f"Keys in Documents of Menu_Items Collection: {mongodb.GetCollection('Menu_Items').find(limit=1).next().keys()}")
# # print(f"Names of Restaurants in DB: {mongodb.GetNamesOfRestaurants()}")
# print(f"Number of Restaurants in in DB: {mongodb.GetNumberOfRestaurants()}")
# print(f"Estimate Document count in Menu_items: {mongodb.GetEstimatedDocumentCount('Menu_Items')}")

# print(mongodb.GetCollectionNames())
# print(f"Documents count in Menu_Items: {mongodb.GetEstimatedDocumentCount()}\n\n")
# for document in mongodb.GetCollection('Menu_Items').find(limit=2):
#     print(document, "\n")



# %%
# mongodb = AllervizDB(db_name='allerviz')
# # mongodb.Load(Path("data/Portland-Honolulu-San_Diego-Grubhub.csv").resolve())
# df = mongodb.LoadData(path="data/Portland-Honolulu-San_Diego-Grubhub.csv",
#                         rtn_df=True,
#                         clean_menu_data=True)
# # df_filtered = df.drop(['item', 'description'], axis = 1)
# # df_filtered = df_filtered.drop_duplicates(subset="restaurant")
# # test = df.groupby("restaurant")
# # df_t = pd.DataFrame()
# # for i,g in enumerate(test.groups):
# #     tmp = test.get_group(g)[["item", "description"]].to_dict("records")
# #     df_t.loc[i,["restaurant", "menu"]] = g, tmp
# # dd = df_filtered.join(df_t.set_index('restaurant'), on='restaurant')

# [test.get_group(x)[[ "item", "description"]].to_dict("records") for x in test.groups)

# df_t.loc[i,["restaurant", "menu"]]

# # Drop menu items and their description to get the top level data of the restaurant
# menu_data = df
# menu_filtered = menu_data.drop(['item', 'description'], axis = 1)
# menu_filtered = menu_filtered.drop_duplicates(subset="restaurant")

# # Initialize new dataframe for grouped menu items
# restaurant_menu_items = pd.DataFrame()
# # Start another DF by grouping on the restaurant name
# print(menu_data.info())
# menu_grouped = menu_data.groupby("restaurant")
# # menu_grouped = menu_data.groupby("restaurant")['street','city', "state", "zip", "latitude", "longitude"].agg(["unique"])
# # menu_grouped = menu_data.groupby("restaurant")['street','city', "state", "zip", "latitude", "longitude"].apply(lambda x: list(np.unique(x)))

# # Iterate over the groups
# for idx, grp in enumerate(menu_grouped.groups):
#     # grab the menu items per restaurant and recordize it to prep for insertion into DB
#     menu_items = menu_grouped.get_group(grp)[["item", "description"]].to_dict("records")

#     # Add to the DF the restaurant name and the list of menu items
#     restaurant_menu_items.loc[idx, ["restaurant", "menu"]] = grp, menu_items

# # Join the dataframes on the restaurant names to add the menu items to the correct restaurant
# reorged_menu_to_restaurants = menu_filtered.join(restaurant_menu_items.set_index('restaurant'), on='restaurant')

