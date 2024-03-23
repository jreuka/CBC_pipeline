import cv2
from tkinter import *
from tkinter import ttk
import random
import os
import argparse
import pandas as pd

from PIL import Image, ImageTk

parser = argparse.ArgumentParser(description="Get paths to video folder, videofilename and out_folder")
parser.add_argument('--results_folder', dest='res_folder', type=str,
                    help='Path to folder holding output from pipeline', default="./")
parser.add_argument('--video_folder', dest='vid_folder', type=str,
                    help='Path to folder holding videos already analysed', default="./")
parser.add_argument('--out_folder', dest='out_folder', type=str,
                    help='Path to save files to (will create a folder when it does not exist)', default="./out/")
parser.add_argument('--out_file', dest='out_f', type=str,
                    help='Path to csv saving output (will create a file when it does not exist)',
                    default="./out/comparison.csv")
                    
parser.add_argument('--with_head_only', dest='who', type=bool,
                    help='boolean value indicating if only images where heads where detected are selected',
                    default=False)

# list of all possible locations
all_locs = ["", "back_left_floor", "front_left_floor", "back_right_floor", "front_right_floor", "front_balcony",
            "mid_balcony", "top_balcony", "back_right_balcony", "back_left_balcony", "left_hose",
            "left_enrichment_house", "back_hose", "back_right_hose", "top_hose", "left_enrichment_pole",
            "mid_hose_enrichment", "back_right_enrichment_hose", "mid_hose", "left_enrichment_tire",
            "back_hose_enrichment", "left_enrichment_tube", "back_enrichment_pole", "left_enrichment_box",
            "right_enrichment_chain", "back_right_swing", "other"]


def main():
    args = parser.parse_args()

    res_path = args.res_folder
    out_path = args.out_folder
    vid_path = args.vid_folder
    out_f = args.out_f
    f_p_vid = 1
    who = args.who

    if not os.path.exists(out_path):
        print("creating folder: ", out_path)
        os.makedirs(out_path)

    if not os.path.isfile(out_f):
        print("creating file: ", out_f)
        out_df = pd.DataFrame({"file_name": [],
                              "frame_number": [],
                              "animal_id": [],
                              "source": [],
                              "location": [],
                              "head_visible": []})
        out_df.to_csv(out_f, index=False)
    else:
        print("reading file: ", out_f)
        out_df = pd.read_csv(out_f)

    class Vid_extractor:

        def __init__(self, v_name, v_path):
            self.vid_name = v_name
            v_path = v_path
            self.cap = cv2.VideoCapture(v_path + vid_name)
            self.tot_f_num = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.saved_imgs = 0
            self.frames = []
            self.btn_val = ""
            self.n_dfname = random.choice([f for f in os.listdir(res_path) if f.endswith(".csv") and "prediction" in f])
            self.stop_pressed = False

        def get_frames(self):
            return self.frames

        def get_savedImgs(self):
            return self.saved_imgs

        def get_tot_f_num(self):
            return self.tot_f_num

        def get_btn_val(self):
            return self.btn_val
        
        def get_stop_pressed(self):
            return self.stop_pressed

        def set_cap(self, f_num):
            self.cap.set(1, f_num)
            return

        def get_frame(self):
            ret, frame = self.cap.read()
            return frame
            
        def get_n_dfname(self):
            return self.n_dfname

        def keep_image(self, f_name, f_num):
            print("Saved image: ", f_name)
            self.frames.append(f_num)
            self.saved_imgs += 1
            print(str(self.saved_imgs), " - images saved")
            return

        def throw_image(self, f_name, f_num):
            print("Saved image: ", f_name)
            self.frames.append(f_num)
            self.saved_imgs += 1
            print(str(self.saved_imgs), " - images saved")
            self.saved_imgs = None
            self.n_dfname = None
            self.stop_pressed = True
            return

        def stop_btn(self, f_name):
            print("Image not used: ", f_name)
            print("Stopped!")
            os.remove(out_path + f_name)
            self.saved_imgs = None
            self.n_dfname = None
        
        def reset_n_dfname(self):
            self.n_dfname = random.choice([f for f in os.listdir(res_path) if f.endswith(".csv") and "prediction" in f])

    df_name = random.choice([f for f in os.listdir(res_path) if f.endswith(".csv") and "prediction" in f])
    while df_name is not None:
        full_name = res_path + df_name
        if pd.read_csv(full_name).empty:
            ve.reset_n_dfname()
            df_name = ve.get_n_dfname()
            continue
        df_res = pd.read_csv(full_name)
        print(full_name)
        assert len(set(df_res['file_name'])) == 1
        vid_name = list(set(df_res['file_name']))[0] + ".mp4"
        print("Path: ", vid_path, "\n", "Video: ", vid_name)
        # Create object
        ve = Vid_extractor(vid_name, vid_path)

        saved = ve.get_savedImgs()
        while saved is not None and saved < f_p_vid:
            # Call random frame number and check if keep or throw
            long_df_res = (pd.melt(df_res[df_res['seg_class'] == 1], id_vars=['frame_number', 'animal_id'],
                                   value_vars=['location']))
            
            if who:
                ls_frms_with_head = [fn for fn in long_df_res['frame_number'].values if 
                (2 in df_res[df_res['frame_number'] == fn]['seg_class'].values)]
                if len(ls_frms_with_head) == 0:
                    ve.reset_n_dfname()
                    df_name = ve.get_n_dfname()
                    saved = None
                    continue
                else:
                    f_num = random.choice(ls_frms_with_head)
            else:
                f_num = random.choice(long_df_res['frame_number'].values)
            # long_df_res[long_df_res.duplicated(subset=['frame_number'])]['frame_number'].values)
            h_vis = int(2 in df_res[df_res['frame_number'] == f_num]['seg_class'].values)
            if f_num in ve.get_frames():
                continue

            # read other cam prediction and check if it matches
            if "left" in full_name:
                ofull_name = full_name.replace("left", "right")
            elif "right" in full_name:
                ofull_name = full_name.replace("right", "left")

            odf_res = pd.read_csv(ofull_name)
            long_odf_res = (pd.melt(odf_res[odf_res['seg_class'] == 1], id_vars=['frame_number', 'animal_id'],
                                   value_vars=['location']))

            if not long_odf_res[long_odf_res['frame_number'] == f_num].reset_index(drop=True).equals(long_df_res[long_df_res['frame_number'] == f_num].reset_index(drop=True)):
                continue

            print(f_num)
            print(ve.get_tot_f_num())

            n_df = pd.DataFrame({
                "file_name": [vid_name[:-4]] * sum(long_df_res['frame_number'] == f_num),
                "frame_number": long_df_res[long_df_res['frame_number'] == f_num]['frame_number'],
                "animal_id": long_df_res[long_df_res['frame_number'] == f_num]['animal_id'],
                "source": long_df_res[long_df_res['frame_number'] == f_num]['variable'],
                "location": long_df_res[long_df_res['frame_number'] == f_num]['value'],
                "head_visible": [h_vis]*sum(long_df_res['frame_number'] == f_num)
            })
            
            print(n_df)
            r_min = int(600/ve.get_tot_f_num() * f_num / 60)
            r_s = ((600/ve.get_tot_f_num() * f_num / 60) - int(600/ve.get_tot_f_num() * f_num / 60)) * 60
            print(r_min, r_s)
            print(len([f for f in os.listdir(out_path) if f.endswith(".png")]))
            if 1 in n_df['animal_id']:
                loc_brmb = n_df[n_df['animal_id'] == 1]['value'].values[0]
            else:
                loc_brmb = ""
            if 2 in n_df['animal_id']:
                loc_brck = n_df[n_df['animal_id'] == 2]['value'].values[0]
            else:
                loc_brck = ""

            # setting up gui
            ws = Tk()
            ws.title('Frame: ' + str(f_num) + ' - Frames_remaining' + str(saved - f_p_vid))
            ws.geometry('450x900')

            f_name = vid_name[:-4] + "_frame_" + str(f_num) + ".png"
            ve.set_cap(f_num)
            frame = ve.get_frame()
            cv2.imwrite(out_path + f_name, frame)
            # get image for gui
            img = Image.open(out_path + f_name)
            img = img.resize((410, 618))
            img = ImageTk.PhotoImage(img)
            Label(ws, image=img).grid(row=1, column=0, columnspan=2, rowspan=4, sticky='NESW')
            # set upo buttons for gui
            btn_1 = Button(ws, text='Save&Next', command=lambda: [ve.keep_image(f_name, f_num), ws.destroy()])
            btn_0 = Button(ws, text='Save&Stop', command=lambda: [ve.throw_image(f_name, f_num), ws.destroy()])
            btn_stop = Button(ws, text='Quit', command=lambda: [ve.stop_btn(f_name), ws.destroy()])

            # label
            ttk.Label(ws, text="Location Bramble:",
                      font=("Times New Roman", 10)).grid(column=0, row=5, padx=10, pady=25)
            # Combobox creation
            n1 = StringVar()
            locchoosen1 = ttk.Combobox(ws, width=27, textvariable=n1)
            # Adding combobox drop down list
            locchoosen1['values'] = (all_locs)
            locchoosen1.grid(column=1, row=5)
            locchoosen1.current(all_locs.index(loc_brmb))

            # label
            ttk.Label(ws, text="Location Bracken:",
                      font=("Times New Roman", 10)).grid(column=0, row=6, padx=10, pady=25)
            # Combobox creation
            n2 = StringVar()
            locchoosen2 = ttk.Combobox(ws, width=27, textvariable=n2)
            # Adding combobox drop down list
            locchoosen2['values'] = (all_locs)
            locchoosen2.grid(column=1, row=6)
            locchoosen2.current(all_locs.index(loc_brck))
            
            # label
            ttk.Label(ws, text="Head visible:",
                      font=("Times New Roman", 10)).grid(column=0, row=7, padx=10, pady=25)
            # Combobox creation
            n3 = StringVar()
            hvisib = ttk.Combobox(ws, width=27, textvariable=n3)
            # Adding combobox drop down list
            hvisib['values'] = (["0","1","2"])
            hvisib.grid(column=1, row=7)
            hvisib.current(1)

            btn_1.grid(row=8, column=1, rowspan=1, columnspan=1, sticky='NESW')
            btn_0.grid(row=8, column=0, rowspan=1, columnspan=1, sticky='NESW')
            btn_stop.grid(columnspan=2, row=0, sticky='NESW')
            ws.mainloop()

            n_df = pd.concat([n_df,
                              pd.DataFrame({
                                  "file_name": [vid_name[:-4]] * 2,
                                  "frame_number": [f_num] * 2,
                                  "animal_id": [1, 2],
                                  "source": ['labelled'] * 2,
                                  "location": [n1.get(), n2.get()],
                                  "head_visible": [n3.get(), n3.get()]
                              })
                              ]).reset_index(drop=True)
            df_name = ve.get_n_dfname()
            print(df_name)
            saved = ve.get_savedImgs()
            
            if df_name is not None and saved is not None:
                out_df = pd.concat([out_df, n_df])
                out_df.to_csv(out_f, index=False)
            elif ve.get_stop_pressed():
                out_df = pd.concat([out_df, n_df])
                out_df.to_csv(out_f, index=False)


if __name__ == "__main__":
    main()
