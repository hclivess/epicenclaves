# EPIC ENCLAVES
_The first blockchain game worth playing_

![Castle Image](img/assets/castle.png)

Coming Soon to NADO and Bismuth

A turn-based strategy game with strong RPG elements, where all graphics are hand-painted, featuring generative item properties and tactical complex battles based on probability. The game is focused on resource management and offers an MMO experience, accommodating an unforeseen amount of players in a browser with an API to integrate freely into any other platforms.

© 2023 Epic Enclaves | Powered by [OpenAI.com](https://openai.com)
All images in this software are proprietary and require a any use of them requires a permission from author.

Structure:

There are two dictionaries and two main databases, structured as follows. usersdb includes positions and all information about players and even their constructed buildings and owned tiles to be displayed in the user panel without minimal performance impact. mapdb includes all information that is displayed on the map (except users). There are two dictionaries because player display is meant to be more detailed while mapdb is supposed to be compact and even limited to a certain number of tiles around the player.

usersdb - data indexed by username:
```
{
   "users":{
      "test":{
         "x_pos":1,
         "y_pos":1,
         "equipped":[
            {
               "type":"axe",
               "damage":1,
               "durability":100,
               "role":"melee"
            }
         ],
         "unequipped":[
            {
               "type":"dagger",
               "damage":2,
               "durability":100,
               "role":"melee"
            }
         ],
         "pop_lim":0,
         "alive":true,
         "online":true
      }
   },
   "construction":{
      "1,1":{
         "type":"boar",
         "role":"enemy",
         "armor":0,
         "max_damage":1
      },
      "1,11":{
         "type":"forest",
         "role":"scenery"
      }
   }
}
```


mapdb - data indexed by x,y:
```
{
   "1,1":{
      "type":"boar",
      "role":"enemy",
      "armor":0,
      "max_damage":1
   },
   "1,21":{
      "type":"forest",
      "role":"scenery"
   }
}
```

user_data.db

x_pos, y_pos, data


map_data.db

x_pos, y_pos, data