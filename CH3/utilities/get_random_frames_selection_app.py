import cv2
from tkinter import *
from tkinter import filedialog
import random
import os
import argparse
from time import sleep
from PIL import Image, ImageTk

parser = argparse.ArgumentParser(description="Get paths to video folder, videofilename and out_folder")
parser.add_argument('--video_folder', dest= 'video_folder', type=str, help='Path to folder holding video to analyse', default="./")
parser.add_argument('--out_folder', dest= 'out_folder', type=str, help='Path to save files to (will create a folder when it does not exist)', default="./out/")
parser.add_argument('--fpvid', dest= 'frames_p_vid', type=int, help='Number of frames saved per video', default=5)
parser.add_argument('--vid_type', dest= 'vid_type', type=str, help='File extensions for videos', default='.mp4')


def main():
	args = parser.parse_args()

	video_path = args.video_folder
	out_path = args.out_folder

	f_p_vid = args.frames_p_vid
	v_type = args.vid_type
	
	if not os.path.exists(out_path): 
		print("creating folder: ", out_path)
		os.makedirs(out_path)
		
	class Vid_extractor:

		def __init__(self, v_name):
			self.vid_name = v_name
			self.cap = cv2.VideoCapture(vid_path + vid_name)
			self.tot_f_num = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
			self.saved_imgs = 0
			self.frames = []
			self.btn_val = ""

		def get_frames(self):
			return self.frames
			
		def get_savedImgs(self):
			return self.saved_imgs
		
		def get_tot_f_num(self):
			return self.tot_f_num
		
		def get_btn_val(self):
			return self.btn_val
			
		def set_cap(self,f_num):
			self.cap.set(1, f_num)
			return
		
		def get_frame(self):
			ret, frame = self.cap.read()
			return frame
		
		def keep_image(self, f_name, f_num):
			print("Saved image: ",f_name)
			self.frames.append(f_num)
			self.saved_imgs +=1
			print(str(self.saved_imgs)," - images saved")
			return

		def throw_image(self, f_name, f_num):
			print("Image not used: ",f_name)
			os.remove(out_path+f_name)
			self.frames.append(f_num)
			return
		
		def stop_btn(self,f_name):
			print("Image not used: ",f_name)
			print("Stopped!")
			os.remove(out_path+f_name)
			self.saved_imgs = None
		
		
	vid_name = "start"
	while vid_name is not ():
		fd = Tk()
		full_name = filedialog.askopenfilename(initialdir=video_path, title="Select file",
                    filetypes=(("video files", "*"+v_type),("all files", "*.*")))
		fd.destroy()
		if full_name is ():
			quit()
		print(full_name)
		vid_path = "/".join(full_name.split("/")[:-1]) + "/"
		vid_name = full_name.split("/")[-1]
		print("Path: ", vid_path, "\n", "Video: ",vid_name)	
		#Create object
		ve = Vid_extractor(vid_name)

		saved = ve.get_savedImgs()
		while saved is not None and saved < f_p_vid:
			#Call random frame number and check if keep or throw
			f_num = random.randrange(ve.get_tot_f_num())
			print(f_num)
			if f_num in ve.get_frames():
				continue
			#setting up gui
			ws = Tk()
			ws.title('Frame: ' + str(f_num) + ' - Frames_remaining'+ str(saved-f_p_vid))
			ws.geometry('450x700')


			f_name = vid_name[:-4] + "_frame_" + str(f_num) +".png"
			ve.set_cap(f_num)
			frame = ve.get_frame()
			cv2.imwrite(out_path+f_name, frame)		
			#get image for gui
			img = Image.open(out_path+f_name)
			img = img.resize((410,618))
			img = ImageTk.PhotoImage(img)
			Label(ws, image=img).grid(row=1,column=0,columnspan=2,rowspan=4,sticky='NESW')
			#set up buttons for gui
			btn_1 = Button(ws, text = 'Keep',command=lambda: [ve.keep_image(f_name, f_num), ws.destroy()])
			btn_0 = Button(ws, text = 'Throw',command=lambda: [ve.throw_image(f_name, f_num), ws.destroy()])
			btn_stop = Button(ws, text = 'Quit', command=lambda: [ve.stop_btn(f_name), ws.destroy()])
			btn_1.grid(row=5,column=1, rowspan=1, columnspan=1,sticky='NESW')
			btn_0.grid(row=5,column=0, rowspan=1, columnspan=1,sticky='NESW')
			btn_stop.grid(columnspan=2,row=0,sticky='NESW')
			ws.mainloop()		
			saved = ve.get_savedImgs()

if __name__ =="__main__":
	main()

