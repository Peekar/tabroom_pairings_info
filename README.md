Project is WIP, code that is ready for the next step is pushed to Github to save online

General idea:

When an email is reviced from Tabroom, send an update to (something, a server likely)

Sever has a list of all tournaments the user is competing at and their dates

Script checks which tournament is going on at the moment, and runs the loading script (if it is the first time) or it will be preloaded 

  The loading script will load all the data needed about the tournament for the later programs (event entries and judges) and save to a tournamnet information file
  
Then the user's latest pairing will be found, and their opponent and judge will be found fromthe tournament information file 

The information above will be link, so then scrapers will be used to get the opponent's record, as well as the judge paradigm

The information is formatted cleanly and returned to the user as an email

