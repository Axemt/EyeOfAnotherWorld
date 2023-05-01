
## Eye Of Another World
<img style="float: left;" src="icon.jpg">

The Destiny 2 project that analyzes weapon stats and perks to predict their popularity

by Jorge Jimenez Garcia, as part of a Bsc in Computer Science for Technological University Dublin</a> 

### How to run

* Gather data
	To gather data, execute the ```weaponCrawler.py``` script to generate a ```.d2data``` file. Control the parameters of the search by modifying the 'PARAMETERS' section of the script
	
* Convert data to a ```.csv```
	Run the ```Preprocess``` notebook. Note that it may need to download the database on first run or if it has been updated since the last execution. Remember to clean leftover databases (```.content``` files)
	
* Train models
	Run the ```Train``` notebook. Computation may take a long time due to the use of 10-Fold Cross Validation
	
* Check for live performance
	With a dataset from a different release, run the ```Cross Release``` notebook. Make sure to convert the dataset to the appropriate feature space and encoding with the provided ```retrofit``` and ```preprocess\_and\_encode``` functions
	
	
### Datasets available

The repository contains data gathered during 'Season of Plunder', 'Season of the Seraph' and 'Lightfall' respectively. It is present in the ```data``` directory, and available in raw and csv formats. Raw formats are to be processed by the ```Preprocess``` notebook again to account for changes in the game's database definitions.
