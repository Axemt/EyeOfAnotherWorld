import os
import time
import webbrowser
import requests
import pickle
from json.decoder import JSONDecodeError
from requests.exceptions import SSLError


DESTINY2_URL = 'https://www.bungie.net/Platform/Destiny2/'
USER_URL = 'https://www.bungie.net/Platform/User/'
GROUP_URL = 'https://www.bungie.net/Platform/GroupV2/'
OAUTH_URL = 'https://www.bungie.net/en/OAuth/Authorize'
TOKEN_URL = 'https://www.bungie.net/Platform/App/OAuth/Token/'
OAUTH_CLIENT_ID = 35713
TOKEN_FILE = ".atok"

PROFILE_INVENTORIES = 102
CHARACTERS = 200
CHARACTER_ACTIVITIES = 204
CHARACTERS_EQUIPMENT = 205
ITEM_STATS = 304
ITEM_PERKS = 302
ITEM_SOCKETS = 305

HASH_MOB = str(2996146975)
HASH_RES = str(392767087)
HASH_REC = str(1943323491)
HASH_DIS = str(1735777505)
HASH_INT = str(144602215)
HASH_STR = str(4244567218)

HASH_RPM = str(4284893193)
HASH_CHARGETIME = str(2961396640)
HASH_DRAWTIME = str(447667954)
HASH_RECHARGESWORD = str(209426660)
HASH_RANGE = str(4188031367)


class DestinyAPI:
    def __init__(self, key):
        self.API_KEY = key
        self.H_API = {'X-API-KEY':'{}'.format(self.API_KEY)}
        self.H_API_AUTH = None
        self.AUTH_TOKEN = None
        self.accountName = None

        self.membershipId = None
        self.lastPlatform = None

        self.timeOfThrottle = 0

    def safeUnwrap(fn):

        def __safeUnwrap(self,*args, **kwargs):
        
            if self.timeOfThrottle > time.time():
                waitTime = self.timeOfThrottle - time.time()
                print('[WARN]: {}: {} ThrottleSeconds remaining, waiting...'.format(time.time(),waitTime))
                time.sleep(waitTime)

            try:
                res = fn(self,*args, **kwargs)
            except JSONDecodeError:
                # The token has expired while processing!
                # re-log in
                print('[WARN]: Unknown JSONDecodeError')
                return {}
            except SSLError:
                # ?
                print('[WARN]: Unknown SSL Error')
                return {}

            while res['ErrorCode'] == 1688:
                # Timeout, retry once
                print('[WARN]: {}: {} :: Retrying query'.format(res['ErrorStatus'],res['Message']))
                res = fn(self, *args, **kwargs)

            while res['ErrorCode'] == 1672:
                # game server throttle
                print('[WARN]: {}: Game Server is throttling :: Retrying query'.format(res['ErrorStatus']))
                time.sleep(30) # wait 30s for the game server to lighten load
                res = fn(self, *args, **kwargs)

            while res['ErrorCode'] == 5:
                # Maintenance
                print('\n[WARN]: {}: Bungie.net is down for maintenance: Waiting 30min\n'.format(res['ErrorStatus']))
                time.sleep(60 * 30)
                res = fn(self, *args, **kwargs)


            if res['ThrottleSeconds'] > 0:
                print('Received ThrottleSeconds: {}'.format(res['ThrottleSeconds']))
                self.timeOfThrottle = time.time() + res['ThrottleSeconds']

            if res['ErrorCode'] == 1665:
                # This user data is private! that's fine though, return empty dict
                # avoid a runtime exception
                print('[WARN]: {}: {}'.format(res['ErrorStatus'],res['Message']))
                return {}
                
            if res['ErrorCode'] != 1:
                print(res)
                emsg = 'Query returned an error code: {}::{}; Reason: {}'.format(res['ErrorCode'], res['ErrorStatus'], res['Message'])
                raise Exception(emsg)

            if 'Response' not in res:
                print(res)
                raise Exception('There was no response ')

            return res['Response']
        
        return __safeUnwrap

    def setAuthToken(self):
        if os.path.exists(TOKEN_FILE):
            if os.path.getctime(TOKEN_FILE) + 3600 > int(time.time()):
                with open(TOKEN_FILE, "rb") as f:
                    auth = pickle.load(f)
            else:
                print("Your login has expired. Please log in again")
                os.remove(TOKEN_FILE)
                exit(-1)


        else:
            auth = OAUTH_URL + f'?client_id={OAUTH_CLIENT_ID}&response_type=code'
            webbrowser.open_new(auth)

            oauth_code = input("A browser window has opened up.\nAuthorize and input the code given by Bungie\n")
            OAUTH_PAYLOAD='grant_type=authorization_code&code={}&client_id={}'.format(oauth_code, OAUTH_CLIENT_ID)
            H_OAUTH = {'Content-Type': 'application/x-www-form-urlencoded'}

            auth = requests.post(TOKEN_URL, headers=H_OAUTH, data=OAUTH_PAYLOAD).json()
            with open(TOKEN_FILE, "wb") as f:
                pickle.dump(auth, f)
            
            if 'access_token' not in auth:
                print("Error! Could not authenticate with Bungie.net; Make sure the code pasted is correct")
                exit(-1)

        self.AUTH_TOKEN = auth['access_token']
        self.accountName = auth['membership_id']
        self.H_API_AUTH = {'X-API-KEY':'{}'.format(self.API_KEY), 'Authorization':'Bearer {}'.format(self.AUTH_TOKEN)}

    def getUserData(self):
        if self.accountName is None:
            self.setAuthToken()
        membershipDataById = USER_URL + 'GetMembershipsById/{}/{}/'.format(self.accountName, -1)
        userData = requests.get(membershipDataById, headers=self.H_API).json()['Response']

        self.lastPlatform = userData['destinyMemberships'][0]['crossSaveOverride']
        self.membershipId = userData['primaryMembershipId']

    @safeUnwrap
    def getProfile(self, optional_fields: list, membershipId=None, platform=None) -> dict:
        if membershipId is None:
           membershipId = self.membershipId
        if platform is None:
           platform = self.platform
        
        getProfile = DESTINY2_URL + '{}/Profile/{}/?components={}'.format(platform, membershipId, ','.join([str(i) for i in optional_fields]))
        profileInfo = requests.get(getProfile, headers=self.H_API).json()
        return profileInfo
    
    @safeUnwrap
    def getExoticsUsage(self, membershipId=None) -> dict:
        if membershipId is None:
           membershipId = self.membershipId 
        
        getExoticsUsed = DESTINY2_URL + '{}/Account/{}/Character/0/Stats/UniqueWeapons'.format(self.lastPlatform, self.membershipId)
        exoticsUsed = requests.get(getExoticsUsed, headers=self.H_API).json()
        return exoticsUsed
    
    @safeUnwrap
    def getActivityHistory(self,characterId: int, membershipId=None,count=20, mode=0,page=0) -> dict:
        if membershipId is None:
           membershipId = self.membershipId 

        getActivityHistory = DESTINY2_URL + '-1/Account/{}/Character/{}/Stats/Activities/?count={}&mode={}&page={}'.format(membershipId, characterId ,count, mode, page)
        activityHistory = requests.get(getActivityHistory, headers=self.H_API).json()
        return activityHistory
    
    @safeUnwrap
    def getPGCR(self, PGCRId: int) -> dict:
        getPGCR = DESTINY2_URL + 'Stats/PostGameCarnageReport/{}/'.format(PGCRId)
        PGCR = requests.get(getPGCR, headers=self.H_API).json()
        return PGCR