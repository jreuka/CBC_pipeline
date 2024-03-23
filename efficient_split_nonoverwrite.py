import os
import subprocess
from moviepy.editor import *
import multiprocessing as mp
from multiprocessing import cpu_count
import time


def get_fnum(vid_name):
    a = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries",
                        "stream=nb_read_packets", "-of", "csv=p=0", vid_name], stdout=subprocess.PIPE)
    fnum = int(a.stdout.decode("UTF-8"))
    return fnum


def conv_crop(vn):
    if os.path.exists(vn[:-5] + "_left.mp4") and os.path.exists(vn[:-5] + "_right.mp4"):
        print(f"{vn} was already converted previously.")
        return

    print(f"Converting {vn}...")
    tic = time.perf_counter()
    v_fps = get_fnum(vn) / 600
    print(vn, v_fps)
    subprocess.run(["MP4Box", "-add", vn + ":fps=" + str(v_fps), vn[:-5] + ".mp4"], stdout=subprocess.PIPE)
    hw = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of",
         "csv=p=0:s=x", vn[:-5] + ".mp4"], stdout=subprocess.PIPE)
    w = hw.stdout.decode("UTF-8")[0:4]
    h = hw.stdout.decode("UTF-8")[5:9]
    subprocess.run(["ffmpeg", "-i", vn[:-5] + ".mp4", "-filter:v", "crop=" + str(int(w) / 2) + ":" + h + ":0:0",
                    vn[:-5] + "_left.mp4", "-loglevel", "quiet"])
    subprocess.run(["ffmpeg", "-i", vn[:-5] + ".mp4", "-filter:v",
                    "crop=" + str(int(w) / 2) + ":" + h + ":" + str(int(w) / 2) + ":0", vn[:-5] + "_right.mp4",
                    "-loglevel", "quiet"])

    os.remove(vn[:-5] + ".mp4")
    toc = time.perf_counter()
    print("convertet in ", toc - tic, " seconds")
    return


def main():
    path = "#PATH TO FOLDER CONTAINING VIDEOS#"
    vid_names = [path + x for x in os.listdir(path) if x.endswith(".h264")]
    print('Starting video conversion')
    print('Using ', cpu_count(), ' cpus')
    p = mp.Pool(cpu_count())
    p.map(conv_crop, vid_names)
    p.join()
    p.close()


if __name__ == '__main__':
    main()
