from utils.DestinyAPI import *
from datetime import datetime
from datetime import date
import json
import pickle
from collections import Counter

#---CONSTANTS---
DATE_FMT = '%Y-%m-%dT%H:%M:%SZ'
PLATFORM_NAMES = ['', 'Xbox', 'PlayStation', 'Steam', 'BattleNet', 'Stadia', 'Epic']
FILE_DUMP_NAME = 'RAD{}MODE{}from{}-to{}.d2data'

# Gamemodes
IB_CONTROL = 43
IB_CLASH = 44
TRIALS = 84
PVP_COMPETITIVE = 69
PVP_QUICKPLAY = 70
#----------------

#---PARAMETERS---

# How many iterations of the algorithm will run
searchRadius = 2

# How many games from each user are logged
countExpansion = 1

date_start = date(2022, 9, 23)
date_end = datetime.today().date()

# The gamemodes to query
modes = [PVP_QUICKPLAY]


# (Optional, modify the start of the snowballing search)
# Players in the open list take the form of tuples where the first component is their Bungie.net ID and the second is their platform
OriginBlock = [(4611686018467559123, 3)]
#---------------



if os.path.exists("D2_TOKEN"):
    with open("D2_TOKEN",'r') as tok:
        D2_TOKEN = tok.read()
else:
    print("You will need an API token to operate the application. Read the README file for instructions")

D2API = DestinyAPI(D2_TOKEN)
del D2_TOKEN




# Snowball Ego Network search
weapons = []

FILE_DUMP_NAME = FILE_DUMP_NAME.format(searchRadius, ''.join([str(i)+'-' for i in modes]), date_start, date_end)
for mode in modes:
    processedCount = 0
    PGCRclosedList = set()
    # Cannot assign! ensure it is a new list every time
    populationIdQueue = [i for i in OriginBlock]
    searchRadius_i = 0
    while searchRadius_i <= searchRadius:
        processedCountLayer = 0
        activityIdQueue = set()
        # Get layer 0, the user
        while len(populationIdQueue) > 0:
            (membId, platform) = populationIdQueue.pop(0)
            # Sometimes, platform can return 0. I think it is for banned accounts
            # See user 4611686018474068937
            if platform == 0:
                print('[RADIUS {} MODE {}]: ID {} Platform: Null, skipping search expansion : {} players in queue'.format(searchRadius_i, mode, membershipId, len(populationIdQueue)))
                continue
            print('[RADIUS {} MODE {}]: ID {} Platform: {:<11}: {} players in queue'.format(searchRadius_i, mode, membId, PLATFORM_NAMES[platform], len(populationIdQueue)))
            
            profile = D2API.getProfile([CHARACTERS,CHARACTER_ACTIVITIES],membershipId=membId, platform=platform)
            
            characters = profile['characters']['data'].keys()

            # TODO: Possible errors if the date range is old and games cannot be found in the first page
            for c in characters:
                
                activityHistory = D2API.getActivityHistory(c,membershipId=membId, mode=mode, count=countExpansion)
                
                if 'activities' in activityHistory:
                    activityHistory = activityHistory['activities']
                    
                    if activityHistory == {}:
                        # Probably private history
                        break
                    
                    for activityInfo in activityHistory:

                        activityDate = datetime.strptime(activityInfo['period'], DATE_FMT).date()
                        if activityDate > date_end or activityDate < date_start:
                            continue

                        activity = activityInfo['activityDetails']['instanceId']
                        if activity not in PGCRclosedList:
                            activityIdQueue.add(activity)
                            break # Found at least one
        

        while len(activityIdQueue) > 0:
            processedCount += 1
            processedCountLayer += 1
            
            PGCRId = activityIdQueue.pop()
            PGCRclosedList.add(PGCRId)
            PGRC = D2API.getPGCR(PGCRId)

            print('\tProcessing PGCR {:11} {}: {} games in queue'.format(PGCRId, PGRC['period'],len(activityIdQueue)))

            for playerInfo in PGRC['entries']:
              
                for w in playerInfo['extended'].get('weapons',[]):
                    # A player may not have any weapon kills in a game, sad!
                        weapons.append( w['referenceId'] )
                
                membershipId = playerInfo['player']['destinyUserInfo']['membershipId']
                platform = playerInfo['player']['destinyUserInfo']['membershipType']
                populationIdQueue.append((membershipId, platform))
        
        print('\nLayer {} search complete:\n\tprocessed {} game instances, of which {} were in this layer\n\tProcessed {} weapons\n\t{} Players in expansion queue\n'.format(searchRadius_i, processedCount, processedCountLayer, len(weapons), len(populationIdQueue)))
        searchRadius_i += 1


print('Processed {} unique games from {} to {}\nGot {} weapon ocurrences of which {} were unique'.format(processedCount, date_start, date_end, len(weapons), len(set(weapons))))

with open(FILE_DUMP_NAME, 'wb') as f:
    print('Writing result data to "{}"...'.format(FILE_DUMP_NAME))
    pickle.dump( (dict(Counter(weapons)), PGCRclosedList) , f)
    print('Dump finished')

