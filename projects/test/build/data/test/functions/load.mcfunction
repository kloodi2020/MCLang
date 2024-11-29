scoreboard objectives add MClangVars dummy {"text": "MCLang Variables"}
scoreboard objectives add MClangTemp dummy {"text": "MCLang Temp"}
scoreboard players set a MClangTemp 52
scoreboard players set b MClangTemp 5
scoreboard players operation a MClangTemp += b MClangTemp
tellraw @a {"score": {"name": "a","objective": "MClangTemp"}}