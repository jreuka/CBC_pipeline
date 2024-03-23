import cv2
import random
import os
import argparse
from time import sleep
from PIL import Image, ImageTk
import numpy as np

parser = argparse.ArgumentParser(description="Get paths to video folder, videofilename and out_folder")
parser.add_argument('--in_folder', dest= 'in_folder', type=str, help='Path to folder holding frames to average', default="./")
parser.add_argument('--out_folder', dest= 'out_folder', type=str, help='Path to save files to (will create a folder when it does not exist)', default="./out/")
parser.add_argument('--out', dest= 'out', type=str, help='Filename of avg IMG', default="AVG_out_IMG.png")


def main():
	args = parser.parse_args()

	in_path = args.in_folder
	out_path = args.out_folder
	out_f = args.out
	firstit = True
	files = [f for f in os.listdir(in_path) if f.endswith(".png") ]
	for i in files:
		frame = cv2.imread(in_path + i)
		if frame.shape != (1232,820,3):
			frame = frame[:,:820,:]
		if firstit:
			average_frame = frame.astype(float)
			firstit = False
		else:
			average_frame += frame.astype(float)
	average_frame /= len(files)
	average_frame = average_frame.astype("uint8")
	# Save blended image
	if out_f.endswith(".png"):
		cv2.imwrite(out_path + out_f, average_frame)
	else:
		cv2.imwrite(out_path + out_f + '.png', average_frame)	

if __name__ =="__main__":
	main()

