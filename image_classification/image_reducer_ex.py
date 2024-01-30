import os
import glob
from PIL import Image

PATH = os.getcwd() + "\\"

jpgList = [f for f in glob.glob("*.JPG")]

for fileName in jpgList:
    #open, resize, optimise, and save
    #foo = Image.open(PATH + fileName)
    #foo = foo.resize((427, 240),Image.ANTIALIAS)
    #foo.save(PATH + "R50-" + fileName,optimize=True,quality=50)
    #foo.save(PATH + "R25-" + fileName,optimize=True,quality=25)
    #foo.save(PATH + "R15-" + fileName,optimize=True,quality=15)
    #foo.save(PATH + "R10-" + fileName,optimize=True,quality=10)

    #open as greyscale, resize, optimise, and save
    bar = Image.open(PATH + fileName).convert('L')
    bar = bar.resize((427, 240),Image.ANTIALIAS)
    #bar.save(PATH + "G50-" + fileName,optimize=True,quality=50)
    #bar.save(PATH + "G25-" + fileName,optimize=True,quality=25)
    bar.save(PATH + "G20-" + fileName,optimize=True,quality=20)
    #bar.save(PATH + "G15-" + fileName,optimize=True,quality=15)
    #bar.save(PATH + "G10-" + fileName,optimize=True,quality=10)