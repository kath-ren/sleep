import torch
import torch.nn as nn
import torchvision.transforms as transforms
import argparse
import numpy as np
import matplotlib.pyplot as plt
import itertools
from tqdm import tqdm
from timm import models
from med import resnet18
from torch.utils.data import Dataset
from torchvision.datasets import ImageFolder
from pathlib import Path
from sklearn.metrics import confusion_matrix, f1_score

LABELS = ["N1", "N2", "N3", "REM", "Wake"]


def test(model, test_loader, criterion, device="cuda"):
    model.eval()

    total = len(test_loader)
    test_correct = 0
    test_loss = 0

    total_labels = []
    total_predicted = []

    for i, (data, labels) in enumerate(tqdm(test_loader, total=total)):
        data = data.float().to(device)
        labels = labels.to(device)

        pred = model(data)
        _, predicted = torch.max(pred, 1)

        test_correct += (predicted == labels).sum().item()

        total_labels.append(labels.detach().cpu().numpy()[0])
        total_predicted.append(predicted.detach().cpu().numpy()[0])

        loss = criterion(pred, labels)
        test_loss += loss.item()

    metrics = confusion_matrix(
        total_labels, total_predicted, labels=[0, 1, 2, 3, 4])
    f1 = f1_score(total_labels, total_predicted, average=None)
    f1_macro = f1_score(total_labels, total_predicted, average='macro')
    f1_micro = f1_score(total_labels, total_predicted, average='micro')
    f1_weighted = f1_score(total_labels, total_predicted, average='weighted')
    plot_confusion_matrix(metrics, classes=LABELS,
                          normalize=False, title='Confusion matrix')
    plot_confusion_matrix(metrics, classes=LABELS,
                          normalize=True, title='Confusion matrix')

    print(f"F1 score : {f1}")
    print(f"F1 socre macro : {f1_macro}")
    print(f"F1 socre micro : {f1_micro}")
    print(f"F1 socre weighted : {f1_weighted}")

    return test_correct, test_loss


def plot_confusion_matrix(cm, classes,
                          normalize=False,
                          title='Confusion matrix',
                          cmap=plt.cm.Blues):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        print("Normalized confusion matrix")
    else:
        print('Confusion matrix, without normalization')

    print(cm)

    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    fmt = '.2f' if normalize else 'd'
    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], fmt),
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")

    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.show()


def main(args):
    DATA_PATH = Path(args.data_path)
    image_size = (128, 1024)

    test_data_path = DATA_PATH / f"{args.channel}_test"

    test_transforms = transforms.Compose([
        transforms.Grayscale(),
        transforms.Resize(image_size),
        transforms.ToTensor(),
    ])

    test_dataset = ImageFolder(root=test_data_path, transform=test_transforms)
    test_loader = torch.utils.data.DataLoader(
        test_dataset, batch_size=args.batch_size, shuffle=True)

    test_total = len(test_loader)

    model = resnet18(num_classes=5).to(args.device)
    # model = models.efficientnet_b3()
    # model.conv_stem = nn.Conv2d(1, 40, kernel_size=(3, 3), stride=(2, 2), padding=(1, 1), bias=False)
    # model.classifier = nn.Linear(in_features=1536, out_features=5, bias=True)
    model.load_state_dict(torch.load(args.load_path)['model_state_dict'])

    model = model.to(args.device)

    criterion = nn.CrossEntropyLoss().to(args.device)

    test_correct, test_loss = test(
        model, test_loader, criterion, device=args.device)
    test_acc = test_correct / (test_total * args.batch_size)
    test_loss = test_loss / (test_total * args.batch_size)
    print(f"[TEST ACC : {test_acc}] | [TEST LOSS : {test_loss}]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_path", default="store/public_dataset")
    parser.add_argument("--load_path", default="./checkpoint/resnet18_pz.pth")
    parser.add_argument("--channel", default="Pz-Oz")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--batch_size", default=1)
    args = parser.parse_args()

    main(args)
