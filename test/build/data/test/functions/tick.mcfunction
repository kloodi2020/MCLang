scoreboard players operation a MClangTemp = x MClangVars
scoreboard players set b MClangTemp 1
scoreboard players operation a MClangTemp += b MClangTemp
scoreboard players operation x MClangVars = a MClangTemp
scoreboard players operation a MClangTemp = x MClangVars
scoreboard players set b MClangTemp 5
execute if score a MClangTemp = b MClangTemp run function test:if_1

tellraw @a {"score": {"name":"x","objective":"MClangVars"}}