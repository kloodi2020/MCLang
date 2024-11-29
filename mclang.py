import os
import configparser

from lexer import Lexer
from parser import Parser
from compiler import Compiler

packFormats = {
    "1.21.3": 61,
    "1.21.1": 57,
    "1.20.6": 48,
    "1.20.4": 41,
    "1.20.2": 26,
    "1.20.1": 18,
    "1.19.4": 15,
    "1.19.3": 12,
    "1.18.2": 10,
    "1.18.1": 9,
    "1.17.1": 8,
    "1.16.5": 7,
    "1.16.1": 6,
    "1.14.4": 5
}

def moveBack(path):
    path = os.path.normpath(path)
    
    split = path.split(os.sep)
    del split[-1]

    result = os.sep.join(split)

    return result

datapackFiles = {
    "pack.mcmeta": "{\"pack\": {\"pack_format\": <fmt>, \"description\": <desc>}}",
}

datapackFiles["data" + os.sep + "minecraft" + os.sep + "tags" + os.sep + "functions" + os.sep + "tick.json"] = "{\"values\": [\"<proj>:tick\"]}"
datapackFiles["data" + os.sep + "minecraft" + os.sep + "tags" + os.sep + "functions" + os.sep + "load.json"] = "{\"values\": [\"<proj>:load\"]}"

def getversion(config, name):
    text = config[name]

    if not "." in text:
        raise ValueError("Invalid version number (example: 1.12)")
    
    result = []
    for part in text.split("."):
        try:
            result.append(int(part))
        except:
            raise ValueError("Invalid version number (example: 1.12)")
    
    return result
def getstring(config, name):
    text = config[name]
    quotes = "\'\""

    if not (text[0] in quotes and text[-1] in quotes):
        raise ValueError("Invalid string")
    
    return text[1:-1]

def getformat(version):
    newVersion = []
    for part in version:
        newVersion.append(str(part))

    versionNum = float("0." + ("").join(newVersion))
    
    for packVersion in packFormats:
        packNum = float("0." + ("").join(packVersion.split(".")))

        if versionNum > packNum:
            return packFormats[packVersion]
    
    return 4

def safeMkDir(path):
    if not os.path.exists(path):
        os.mkdir(path)

def build(projName):
    projectFolder = moveBack(__file__) + os.sep + "projects" + os.sep + projName
    if os.path.exists(projectFolder):
        functionPath = projectFolder + os.sep + "build" + os.sep + "data" + os.sep + projName + os.sep + "functions"
        safeMkDir(projectFolder + os.sep + "build" + os.sep + "data")

        safeMkDir(projectFolder + os.sep + "build" + os.sep + "data" + os.sep + "minecraft")
        safeMkDir(projectFolder + os.sep + "build" + os.sep + "data" + os.sep + "minecraft" + os.sep + "tags")
        safeMkDir(projectFolder + os.sep + "build" + os.sep + "data" + os.sep + "minecraft" + os.sep + "tags" + os.sep + "functions")

        safeMkDir(projectFolder + os.sep + "build" + os.sep + "data" + os.sep + projName)
        safeMkDir(functionPath)

        files = [functionPath + os.sep + file for file in os.listdir(functionPath) if os.path.isfile(os.path.join(functionPath, file))]
        for file in files:
            os.remove(file)

        config = configparser.ConfigParser()
        filePath = projectFolder + os.sep + "src" + os.sep + "config.cfg"
        
        config.read(filePath)

        version = getversion(config["pack"], "version")
        desc = getstring(config["pack"], "description")

        useVars = {
            "fmt": getformat(version),
            "desc": f"\"{desc}\"",
            "proj": projName
        }

        for filePath in datapackFiles:
            text = datapackFiles[filePath]
            for key in useVars:
                text = text.replace(f"<{key}>", f"{useVars[key]}")

            with open(projectFolder + os.sep + "build" + os.sep + filePath, "w") as file:
                file.write(text)

        filePath = projectFolder + os.sep + "src" + os.sep + "main.mclang"

        if os.path.isfile(filePath):
            with open(filePath, "r") as fileIO:
                code = fileIO.read()
            
            lexer = Lexer(file, code)
            tokens, error = lexer.lex()

            if error:
                print("An error occured during lexing.")
                print(str(error))
                exit()
            
            print(tokens)

            parser = Parser(tokens)
            ast = parser.parse()

            if ast.error:
                print("An error occured during parsing.")
                print(str(ast.error))
                exit()

            print(ast.node)

            compiler = Compiler(functionPath, projName)

            print(compiler.visit(ast.node))
    else:
        print("Project folder does not exist!")

build("test")