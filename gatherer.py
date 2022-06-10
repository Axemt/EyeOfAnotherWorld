#import pydest as destiny #Pydest is bad and old
import webbrowser
import requests
import os
from datetime import date
import time
import numpy as np
import pickle

DESTINY2_URL = 'https://www.bungie.net/Platform/Destiny2/'
USER_URL = 'https://www.bungie.net/Platform/User/'
GROUP_URL = 'https://www.bungie.net/Platform/GroupV2/'
OAUTH_URL = 'https://www.bungie.net/en/OAuth/Authorize'
TOKEN_URL = 'https://www.bungie.net/Platform/App/OAuth/Token/'
OAUTH_CLIENT_ID = 35713
TOKEN_FILE = ".atok"

PROFILE_INVENTORIES = 102
CHARACTERS = 200
CHARACTERS_EQUIPMENT = 205
ITEM_STATS = 304

HASH_MOB = str(2996146975)
HASH_RES = str(392767087)
HASH_REC = str(1943323491)
HASH_DIS = str(1735777505)
HASH_INT = str(144602215)
HASH_STR = str(4244567218)

if os.path.exists("D2_TOKEN"):
    with open("D2_TOKEN",'r') as tok:
        D2_TOKEN = tok.read()
else:
    print("You will need an API token to operate the application. Read the README file for instructions")
H_API = {'X-API-KEY':'{}'.format(D2_TOKEN)}

AUTH_TOKEN = None
#Get OAuth2 token
if os.path.exists(TOKEN_FILE):
    if os.path.getctime(TOKEN_FILE) + 3600 > int(time.time()):
        with open(TOKEN_FILE, "rb") as f:
            AUTH_TOKEN = pickle.load(f)
    else:
        print("Your login has expired. Please log in again")
        os.remove(TOKEN_FILE)


if AUTH_TOKEN == None:
    auth = OAUTH_URL + f'?client_id={OAUTH_CLIENT_ID}&response_type=code'
    webbrowser.open_new(auth)

    oauth_code = input("A browser window has opened up.\nAuthorize and input the code given by Bungie\n")
    OAUTH_PAYLOAD='grant_type=authorization_code&code={}&client_id={}'.format(oauth_code, OAUTH_CLIENT_ID)
    H_OAUTH = {'Content-Type': 'application/x-www-form-urlencoded'}

    AUTH_TOKEN = requests.post(TOKEN_URL, headers=H_OAUTH, data=OAUTH_PAYLOAD).json()
    with open(TOKEN_FILE, "wb") as f:
        pickle.dump(AUTH_TOKEN, f)
    
    if 'access_token' not in AUTH_TOKEN:
        print("Error! Could not authenticate with Bungie.net; Make sure the code pasted is correct")
        exit(-1)


uname = AUTH_TOKEN['membership_id']
AUTH_TOKEN = AUTH_TOKEN['access_token']
H_API_AUTH = {'X-API-KEY':'{}'.format(D2_TOKEN), 'Authorization':'Bearer {}'.format(AUTH_TOKEN)}




membershipDataById = USER_URL + 'GetMembershipsById/{}/{}/'.format(uname, -1)
userData = requests.get(membershipDataById, headers=H_API).json()['Response']

print("Logged in as {}".format(userData['bungieNetUser']['uniqueName']))

lastPlatform = userData['destinyMemberships'][0]['crossSaveOverride']
membershipId = userData['primaryMembershipId']
getProfile = DESTINY2_URL + '{}/Profile/{}/?components={}'.format(lastPlatform, membershipId, ','.join([str(i) for i in [PROFILE_INVENTORIES, ITEM_STATS]]))
profile = requests.get(getProfile, headers=H_API_AUTH).json()['Response']

equippable = profile['itemComponents']['stats']['data']

toClassify = input("How many items do you want to classify? (leave empty for \'all\'): ")
if toClassify == "":
    N = len(equippable)
else:
    N = min(int(toClassify), len(equippable))

ARMOR_CONTENTFILE = "items-{}.npy".format(userData['bungieNetUser']['uniqueName'])
TAGS_CONTENTFILE = "tags-{}.npy".format(userData['bungieNetUser']['uniqueName'])

if os.path.exists(ARMOR_CONTENTFILE) and os.path.exists(TAGS_CONTENTFILE):
    armor = np.load(ARMOR_CONTENTFILE)
    tags = np.load(TAGS_CONTENTFILE)
else:
    armor = np.zeros( (1,6) )
    tags  = np.zeros( (1,) )

ct = 0
print(f"Classifying {N} items...\n")
for item in equippable.values():
    if HASH_INT in item['stats']: #Is an armor piece
        mob  = int(item['stats'][HASH_MOB]['value'])
        res  = int(item['stats'][HASH_RES]['value'])
        rec  = int(item['stats'][HASH_REC]['value'])
        dis  = int(item['stats'][HASH_DIS]['value'])
        inte = int(item['stats'][HASH_INT]['value'])
        stre = int(item['stats'][HASH_STR]['value'])

        stat_total = mob + res + rec + dis + inte + stre
        armorpiece = np.array([mob, res, rec, dis, inte, stre])

        is_contained = (armor == armorpiece).all(axis=1).any()

        if ct < N and stat_total > 50 and not is_contained:
            print("Armor piece with:")
            print(f"\t{mob} Mobility")
            print(f"\t{res} Resilience")
            print(f"\t{rec} Recovery")
            print(f"\t{dis} Discipline")
            print(f"\t{inte} Intellect")
            print(f"\t{stre} Strength\n")
            print(f"Stat total: {stat_total}")

            clas = int(input("Is it a good armor piece?\n\t[1] Yes\n\t[2] No\n"))

            #add new row           
            armor = np.vstack( (armor, np.array([mob, res, rec, dis, inte, stre]) ) )
            tags = np.vstack( (tags, clas) )

            if os.name == 'nt':
                os.system('cls')
            # for mac and linux(here, os.name is 'posix')
            else:
                os.system('clear')
            ct += 1

            if ct == N:
                break
        else:
            continue

if os.path.exists(ARMOR_CONTENTFILE) and os.path.exists(TAGS_CONTENTFILE):
    os.remove(ARMOR_CONTENTFILE)
    os.remove(TAGS_CONTENTFILE)

np.save(ARMOR_CONTENTFILE, armor)
np.save(TAGS_CONTENTFILE, tags)
