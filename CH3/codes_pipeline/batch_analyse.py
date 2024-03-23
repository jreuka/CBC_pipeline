import pandas as pd
import torch
from ultralytics import YOLO
import pickle
import os
import time
from datetime import date

from custom_functions import predict_id_hp_location_hardcoded
from custom_functions import convert_objcts2dataframe
from custom_plot_functions import plot_videos


out_path = "#PATH TO DIR TO SAVE RESULTS TO"

vid_folder = "PATH TO FOLDER HOLDING VIDEOS"

yolo_model_path = "./yolov8_CBC_segmodel.pt" # path to trained yolov8 model

tracker_path = "custom_tracker_bots.yaml" # path to tracker yaml file

vid_paths = [vid_folder + v for v in os.listdir(vid_folder) if v.endswith(".mp4")]
vid_paths = sorted(vid_paths)

#outputs time taken to analyse videos
path_df_analysistime = out_path + "analysis_time_batch_analyse_1.csv"
if os.path.isfile(path_df_analysistime):
    df_analysistime = pd.read_csv(path_df_analysistime)
else:
    df_analysistime = pd.DataFrame(
        columns=['date_analysed', 'vid_path', 'file_name', 'time_analysed', 'num_tracks', 'num_masks'])

# Load a model
model = YOLO(yolo_model_path)

for vid_path in vid_paths:
    if os.path.exists(out_path + "prediction_" + vid_path.split("/")[-1][:-4] + ".pkl") and os.path.exists(out_path + "prediction_" + vid_path.split("/")[-1][:-4] + ".csv"):
        print(f"{vid_path} already analysed is skipped ...")
        continue
    print(f"Predicting {vid_path} ...")
    ts = time.time()
    # Predict with the model
    results = model.track(vid_path, conf=0.5, iou=0.3, tracker=tracker_path, stream=True, max_det=5,
                          verbose=False)
    tr_info, msx = predict_id_hp_location_hardcoded(results, vid_path)
    # Save in pkl file
    out_ls = [tr_info, msx]
    with open(out_path + "prediction_" + vid_path.split("/")[-1][:-4] + ".pkl", "wb") as f:
        pickle.dump(out_ls, f)

    # save as csv file
    df = convert_objcts2dataframe(tr_info, msx)
    df['file_name'] = vid_path.split("/")[-1].split(".")[0]
    df.to_csv(out_path + "prediction_" + vid_path.split("/")[-1][:-4] + ".csv")

    df_analysistime = pd.concat([df_analysistime, pd.DataFrame.from_records([
        {'date_analysed': date.today(),
         'file_path': vid_path,
         'file_name': vid_path.split("/")[-1].split(".")[0],
         'time_analysed': time.time() - ts,
         'num_tracks': tr_info.shape[1] if type(tr_info) == torch.Tensor else len(tr_info),
         'num_masks': len(msx)
         }
    ])])
    # plot videos
    # if len(tr_info) != 0 and len(msx) !=0:
    #    plot_videos(vid_path, tr_info, msx, save_dir=out_path, with_ID=True, with_location=False)
    df_analysistime.to_csv(path_df_analysistime)
