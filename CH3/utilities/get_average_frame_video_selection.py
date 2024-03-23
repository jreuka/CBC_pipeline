import cv2
import random
import os
import argparse
from time import sleep
from PIL import Image, ImageTk
import numpy as np

parser = argparse.ArgumentParser(description="Get paths to video folder, videofilename and out_folder")
parser.add_argument('--video_folder', dest= 'video_folder', type=str, help='Path to folder holding video to analyse', default="./")
parser.add_argument('--out_folder', dest= 'out_folder', type=str, help='Path to save files to (will create a folder when it does not exist)', default="./out/")
parser.add_argument('--vid_type', dest= 'vid_type', type=str, help='File extensions for videos', default='.mp4')
parser.add_argument('--fpv', dest= 'fpv', type=int, help='Frames to average over per video', default=36)

def main():
	args = parser.parse_args()

	video_path = args.video_folder
	out_path = args.out_folder

	v_type = args.vid_type
	
	if not os.path.exists(out_path): 
		print("creating folder: ", out_path)
		os.makedirs(out_path)
		

	for full_name in [f for f in os.listdir(video_path) if f.endswith(v_type)]:
		print(full_name)
		vid_path = video_path
		vid_name = full_name.split("/")[-1]
		print("Path: ", vid_path, "\n", "Video: ",vid_name)	
		
		cap = cv2.VideoCapture(vid_path + vid_name)
		tot_f_num = cap.get(cv2.CAP_PROP_FRAME_COUNT)
		
		
		for i in range(args.fpv):
			f_num = random.randrange(tot_f_num)
			_, frame = cap.read()
			if i == 0:
				average_frame = frame.astype(float)
			else:
				average_frame += frame.astype(float)
		average_frame /= args.fpv
		average_frame = average_frame.astype("uint8")
		# Save blended image
		cv2.imwrite(out_path+ 'AvgIMG_'+vid_name[:-4] + '.png', average_frame)	

if __name__ =="__main__":
	main()

