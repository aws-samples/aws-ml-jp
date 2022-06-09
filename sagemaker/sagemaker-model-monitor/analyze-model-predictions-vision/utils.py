import numpy as np
import matplotlib.pyplot as plt
from torchvision import datasets, models, transforms
import torch.utils.data.dataloader as Data
import torch.nn as nn
import torch
import os
import cv2
import imageio

def get_dataloader():
    val_transform = transforms.Compose([
        transforms.Resize((128, 128)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    dataset = datasets.ImageFolder("GTSRB/Final_Test/", val_transform)
    val_dataloader = torch.utils.data.DataLoader(dataset, batch_size=1, shuffle=True)

    return val_dataloader

def load_model():
    #check if GPU is available and set context
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    #load model
    model = models.resnet18()

    #traffic sign dataset has 43 classes
    nfeatures = model.fc.in_features
    model.fc = nn.Linear(nfeatures, 43)

    weights = torch.load('model/model.pt', map_location=lambda storage, loc: storage)
    model.load_state_dict(weights)

    for param in model.parameters():
        param.requires_grad = False

    model.to(device).eval()
    return model


def show_images_diff(image, adv_image, adv_label, signnames, index):
    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]

    adv_image = adv_image.transpose(1, 2, 0)
    adv_image = (adv_image * std) + mean
    adv_image = adv_image * 255.0
    adv_image = np.clip(adv_image, 0, 255).astype(np.uint8)

    image = image.cpu().numpy()[0,:,:,:]
    image = image.transpose(1, 2, 0)
    image = (image * std) + mean
    image = image * 255.0
    image = np.clip(image, 0, 255).astype(np.uint8)

    plt.figure(figsize=(10, 15))

    plt.subplot(131)
    plt.title('Original')
    plt.imshow(image)
    plt.axis('off')

    plt.subplot(132)
    plt.title(f'Model prediction: {signnames[adv_label]}')
    plt.imshow(adv_image)
    plt.axis('off')

    plt.subplot(133)
    plt.title('Diff')
    difference = adv_image - image

    difference = difference / abs(difference).max() / 2.0 + 0.5

    plt.imshow(difference, cmap=plt.cm.gray)
    plt.axis('off')
    plt.tight_layout()
    plt.show()

    imageio.imwrite(f'adversarial_examples/{index}.png', adv_image)


def plot_saliency_map(saliency_map, image, predicted_class, probability, signnames):

    #clear matplotlib figure
    plt.clf()

    #revert normalization
    mean = [[[0.485]], [[0.456]], [[0.406]]]
    std = [[[0.229]], [[0.224]], [[0.225]]]
    image = image * std + mean

    #transpose image: color channel in last dimension
    image = image.transpose(1, 2, 0)
    image = (image * 255).astype(np.uint8)

    #create heatmap: we multiply it with -1 because we use
    # matplotlib to plot output results which inverts the colormap
    saliency_map = - saliency_map * 255
    saliency_map = saliency_map.astype(np.uint8)
    heatmap = cv2.applyColorMap(saliency_map, cv2.COLORMAP_JET)

    #overlay original image with heatmap
    output_image = heatmap.astype(np.float32) + image.astype(np.float32)

    #normalize
    output_image = output_image / np.max(output_image)

    #plot
    fig, (ax0, ax1) = plt.subplots(ncols=2, figsize=(10, 5))
    ax0.imshow(image)
    ax1.imshow(output_image)
    ax0.set_axis_off()
    ax1.set_axis_off()
    ax0.set_title('Input image')
    ax1.set_title('Predicted class {} ({}) with probability {}%'.format(
        predicted_class,
        signnames[predicted_class],
        probability,
    ))
    plt.show()
