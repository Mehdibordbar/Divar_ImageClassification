import glob
import pandas as pd

import csv

with open('Image_Labels.csv', mode='w', newline='') as csv_file:
    fieldnames = ['Image_name','Class']
    writer = csv.DictWriter(csv_file, fieldnames = fieldnames)

    writer.writeheader()
    for image_path in glob.glob("Dataset/*/*.jpg"):
        splitted = image_path.split('\\')
        writer.writerow({'Image_name':splitted[2],'Class':splitted[1]})
