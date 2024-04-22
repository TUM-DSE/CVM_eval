# This PyTorch image classification example is based off
# https://www.learnopencv.com/pytorch-for-beginners-image-classification-using-pre-trained-models/

import sys
import time
import os
from pathlib import Path

from torchvision import models
import torch

# Load the model from a file
alexnet = torch.load("alexnet-pretrained.pt")

# Prepare a transform to get the input image into a format (e.g., x,y dimensions) the classifier
# expects.
from torchvision import transforms
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(
    mean=[0.485, 0.456, 0.406],
    std=[0.229, 0.224, 0.225]
)])

# Load the image.
from PIL import Image
img = Image.open("input.jpg")

if len(sys.argv) != 3:
    print("Usage: ptyhon pytorchexample.py <cpu_count> <experiment_label>")
    sys.exit(1)

try:
    cpu_count = int(sys.argv[1])
except ValueError:
    print("Error: CPU count must be an int!")
    sys.exit(1)

experiment_label = sys.argv[2]

# set OMP_NUM_THREADS to the cpu count for the parallel execution
os.environ["OMP_NUM_THREADS"] = str(cpu_count)
torch.set_num_threads(cpu_count)
print("Number of threads: %d" % torch.get_num_threads(), flush=True)

start_time = time.time()

for i in range(0, 1000):
    # Apply the transform to the image.
    img_t = transform(img)

    # Magic (not sure what this does).
    batch_t = torch.unsqueeze(img_t, 0)

    # Prepare the model and run the classifier.
    alexnet.eval()
    out = alexnet(batch_t)

    # Sort the predictions.
    _, indices = torch.sort(out, descending=True)

    # Convert into percentages.
    percentage = torch.nn.functional.softmax(out, dim=1)[0] * 100

print("--- %.2f seconds ---" % (time.time() - start_time), flush=True)

# Print the exec time.
result_path = Path("results")
result_path.mkdir(parents=True, exist_ok=True)
with open("results/"+experiment_label+"_"+str(cpu_count)+"_threads.txt", "w") as outfile:
    outfile.write(str(time.time() - start_time) + " seconds\n")
    outfile.flush()
    os.fsync(outfile.fileno())
print("The execution time result was written to results/"+experiment_label+"_"+str(cpu_count)+"_threads.txt` .")

# Load the classes from disk.
with open('classes.txt') as f:
    classes = [line.strip() for line in f.readlines()]

# Print the 5 most likely predictions.
with open("result.txt", "w") as outfile:
    outfile.write(str([(classes[idx], percentage[idx].item()) for idx in indices[0][:5]]))
    outfile.flush()
    os.fsync(outfile.fileno())
print("Done. The result was written to `result.txt`.")
