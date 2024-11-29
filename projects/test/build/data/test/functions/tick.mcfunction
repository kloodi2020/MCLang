scoreboard players operation a MClangTemp = x MClangVars
scoreboard players set b MClangTemp 1
scoreboard players operation a MClangTemp += b MClangTemp
scoreboard players operation x MClangVars = a MClangTemp

tellraw @a {"score": {"name": "x","objective": "MClangVars"}}