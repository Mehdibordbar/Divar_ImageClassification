# -*- coding: utf-8 -*-
"""Bordbar_Project.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/18dW3nedFuEtvEOiz_YtvSL2y-b9MthL4

# Final Project
Student : Mehdi Bordbar
"""

!wget "https://ndownloader.figshare.com/articles/13909202/versions/1" -O files.zip

!unzip files.zip

!unzip Dataset.zip

from __future__ import print_function, division
import os
import torch
import pandas as pd
from skimage import io, transform
import numpy as np
import matplotlib.pyplot as plt
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, utils, datasets, models
import glob
from PIL import Image
from torch import nn
from torch import optim
import torchvision

classes = {0:'Dena_Plus' , 1:'MG' , 2:'peugeot_206' , 3:'Quick' , 4:'Samand_LX', 5:'Tiba_Hatchback'}
Classes_inv = {v: k for k, v in classes.items()}

class CarDataset(Dataset):
    """Face Landmarks dataset."""

    def __init__(self, csv_file, root_dir, transform=None):
        """
        Args:
            csv_file (string): Path to the csv file with annotations.
            root_dir (string): Directory with all the images.
            transform (callable, optional): Optional transform to be applied
                on a sample.
        """
        self.classes = pd.read_csv(csv_file)
        self.dataset = glob.glob(root_dir + '*/*.jpg')
        self.transform = transform

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        image_path = self.dataset[idx]
        image_name = image_path.split("/")[-1]
        image = Image.open(image_path)
        image_info = self.classes.loc[self.classes['Image_name'] == image_name]
        target = image_info['Class'].item()
        target = Classes_inv[target]
        if self.transform:
            image = self.transform(image)
        return image , target

i_transform=transforms.Compose([transforms.ToTensor()])
Car_dataset = CarDataset(csv_file='Image_Labels.csv',root_dir='Dataset/',transform=i_transform)

df = pd.read_csv('Image_Labels.csv')
labels = df['Class'].tolist()

len(Car_dataset)

train_set, val_set , test_set = torch.utils.data.random_split(Car_dataset, [1900 , 100 , 155])
train_loader = DataLoader(train_set , shuffle=True , num_workers= 4 , batch_size= 64)
val_loader = DataLoader(val_set , shuffle=False , num_workers= 0 , batch_size= 1)
test_loader = DataLoader(test_set , shuffle=False , num_workers= 0 , batch_size= 1)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def imshow(img):
    img = img / 2 + 0.5     # unnormalize
    npimg = img.numpy()
    plt.imshow(np.transpose(npimg, (1, 2, 0)))
    plt.show()


# get some random training images
dataiter = iter(train_loader)
images, labels = dataiter.next()

# show images
imshow(torchvision.utils.make_grid(images))
# print labels
print('    '.join('%5s' % classes[labels.tolist()[j]] for j in range(4)))

"""## Model Number 1 : ResNet50 pretrained by ImageNET"""

model = models.resnet50(pretrained=True)
print(model)

for param in model.parameters():
    param.requires_grad = False
    
model.fc = nn.Sequential(nn.Linear(2048, 512),
                                 nn.ReLU(),
                                 nn.Dropout(0.2),
                                 nn.Linear(512, 6))
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.fc.parameters(), lr=0.003)
model.to(device)

epochs = 20
steps = 0
running_loss = 0
print_every = 10
train_losses, test_losses = [], []
for epoch in range(epochs):
    for inputs, labels in train_loader:
        steps += 1
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        logps = model.forward(inputs)
        loss = criterion(logps, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item()
        
        if steps % print_every == 0:
            test_loss = 0
            accuracy = 0
            model.eval()
            with torch.no_grad():
                for inputs, labels in val_loader:
                    inputs, labels = inputs.to(device),labels.to(device)
                    logps = model.forward(inputs)
                    batch_loss = criterion(logps, labels)
                    test_loss += batch_loss.item()
                    
                    ps = torch.exp(logps)
                    top_p, top_class = ps.topk(1, dim=1)
                    equals = top_class == labels.view(*top_class.shape)
                    accuracy += torch.mean(equals.type(torch.FloatTensor)).item()
            train_losses.append(running_loss/len(train_loader))
            test_losses.append(test_loss/len(val_loader))                    
            print(f"Epoch {epoch+1}/{epochs}.. "
                  f"Train loss: {running_loss/print_every:.3f}.. "
                  f"val loss: {test_loss/len(val_loader):.3f}.. "
                  f"val accuracy: {accuracy/len(val_loader):.3f}")
            running_loss = 0
            model.train()
torch.save(model, 'DivarCar.pth')

from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns
y_pred_list = []
y_gt_list = []

with torch.no_grad():
    model.eval()
    for inputs, labels in test_loader:
      inputs, labels = inputs.to(device),labels
      logps = model(inputs)
      y_pred_list.append(classes[np.argmax(logps[0].cpu().detach().numpy())])
      y_gt_list.append(classes[int(labels[0].cpu().detach().numpy())])
      # print('=====================================')
      # print(classes[int(labels[0].cpu().detach().numpy())])
      # print(classes[np.argmax(logps[0].cpu().detach().numpy())])

confusion_matrix_df = pd.DataFrame(confusion_matrix(y_gt_list, y_pred_list)).rename(columns=classes, index=classes)

sns.heatmap(confusion_matrix_df, annot=True)

print(classification_report(y_gt_list, y_pred_list))

"""## Model Number 2 : inception V3 pretrained by ImageNet"""

models.inception_v3(pretrained=True)
print(model)

for param in model.parameters():
    param.requires_grad = False
    
model.fc = nn.Sequential(nn.Linear(2048, 512),
                                 nn.ReLU(),
                                 nn.Dropout(0.2),
                                 nn.Linear(512, 6))
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.fc.parameters(), lr=0.003)
model.to(device)

epochs = 20
steps = 0
running_loss = 0
print_every = 10
train_losses, test_losses = [], []
for epoch in range(epochs):
    for inputs, labels in train_loader:
        steps += 1
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        logps = model.forward(inputs)
        loss = criterion(logps, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item()
        
        if steps % print_every == 0:
            test_loss = 0
            accuracy = 0
            model.eval()
            with torch.no_grad():
                for inputs, labels in val_loader:
                    inputs, labels = inputs.to(device),labels.to(device)
                    logps = model.forward(inputs)
                    batch_loss = criterion(logps, labels)
                    test_loss += batch_loss.item()
                    
                    ps = torch.exp(logps)
                    top_p, top_class = ps.topk(1, dim=1)
                    equals = top_class == labels.view(*top_class.shape)
                    accuracy += torch.mean(equals.type(torch.FloatTensor)).item()
            train_losses.append(running_loss/len(train_loader))
            test_losses.append(test_loss/len(val_loader))                    
            print(f"Epoch {epoch+1}/{epochs}.. "
                  f"Train loss: {running_loss/print_every:.3f}.. "
                  f"val loss: {test_loss/len(val_loader):.3f}.. "
                  f"val accuracy: {accuracy/len(val_loader):.3f}")
            running_loss = 0
            model.train()
torch.save(model, 'DivarCar2.pth')

from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns
y_pred_list = []
y_gt_list = []

with torch.no_grad():
    model.eval()
    for inputs, labels in test_loader:
      inputs, labels = inputs.to(device),labels
      logps = model(inputs)
      y_pred_list.append(classes[np.argmax(logps[0].cpu().detach().numpy())])
      y_gt_list.append(classes[int(labels[0].cpu().detach().numpy())])
      # print('=====================================')
      # print(classes[int(labels[0].cpu().detach().numpy())])
      # print(classes[np.argmax(logps[0].cpu().detach().numpy())])

confusion_matrix_df = pd.DataFrame(confusion_matrix(y_gt_list, y_pred_list)).rename(columns=classes, index=classes)

sns.heatmap(confusion_matrix_df, annot=True)

print(classification_report(y_gt_list, y_pred_list))

"""## Model Number 3 : Decision Tree"""

t_transform = transforms.Compose([
                                  transforms.Resize((16,16)),
                                  transforms.ToTensor()
])
dataset = CarDataset('Image_Labels.csv','Dataset/',t_transform)

train_set, val_set , test_set = torch.utils.data.random_split(dataset, [1900 , 100 , 155])
train_loader = DataLoader(train_set , shuffle=True , num_workers= 4 , batch_size= 1)
val_loader = DataLoader(val_set , shuffle=False , num_workers= 0 , batch_size= 1)
test_loader = DataLoader(test_set , shuffle=False , num_workers= 0 , batch_size= 1)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

img,target = next(iter(dataloader))
plt.imshow(img[0].permute(1,2,0))

df = pd.DataFrame(columns=['Pixel_' + str(x) for x in range(256*3)] + ['target'])
for img,target in train_loader:
  img = torch.reshape(img[0] , (256*3,))
  new_data = pd.Series(img.tolist() + [classes[int(target)]], index = df.columns)
  df = df.append(new_data, ignore_index=True)
df.head(5)

import pandas as pd
from sklearn import tree
import pydotplus
from sklearn.tree import DecisionTreeClassifier
import matplotlib.pyplot as plt
import matplotlib.image as pltim
import matplotlib.image as pltimg
import numpy as np

X = df.iloc[:,0:768]
Y = df.iloc[:,-1]

dtree = DecisionTreeClassifier()
dtree = dtree.fit(X, Y)
data = tree.export_graphviz(dtree, out_file=None, feature_names=X.columns,class_names= list(classes.values()),filled=True, rounded=True,  
                      special_characters=True)
graph = pydotplus.graph_from_dot_data(data)
graph.write_png('mydecisiontree.png')

img=pltimg.imread('mydecisiontree.png')
imgplot = plt.imshow(img , aspect='auto')
plt.show()

pred = []
gt = []
for img,target in test_loader:
  img = torch.reshape(img[0] , (256*3,))
  new_data = pd.Series(img.tolist(), index = df.columns[0:768])
  gt.append(classes[int(target)])
  pred.append(dtree.predict([new_data])[0])

print(gt)

print(pred)

from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns

confusion_matrix_df = pd.DataFrame(confusion_matrix(gt, pred)).rename(columns=classes, index=classes)

sns.heatmap(confusion_matrix_df, annot=True)

print(classification_report(gt, pred))

