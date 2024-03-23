import cv2
from tqdm import tqdm


def plot_videos(vid_file, tr_info, msx, video_out_name=None, save_dir="./", with_ID=True, with_location=False,
                conf_filter=None):
    """
    Function to match boxes of different classes together to identify animals with and without HP
    :param
    vid_file: path to video file to plot
    tr_info: tr_info tensor - tensor[tr_A-id/tr_cl/tr_conf, tr_id] - see output from overlap_tracks_by_class
    msx: mask dictionary - dict{Frame_Number}[Track_IDs, [mask segments]] - see output from overlap_tracks_by_class
    video_out_name: name of output video - default None - will use original name with prefix "prediction_"
    save_dir: directory to save output video - default "./"
    with_ID: if plotted videos should include ID label - default True
    with_location: if plotted videos should include location label - default False
    :return:
            - prints created statement and will create video file in given directory
    """
    cat_conv_col = {
        0: (255, 0, 0),
        1: (255, 255, 0),
        2: (127, 255, 0)
    }
    # TODO
    a_id_conv = {
        2: "Animal2",
        1: "Animal1",
        0: "Unsure",
        3: "CLOSE_BOTH"
    }

    if video_out_name is None:
        video_out_name = "prediction_" + vid_file.split("/")[-1]

    cap = cv2.VideoCapture(vid_file)
    fps_set = cap.get(cv2.CAP_PROP_FPS)
    print("FPS:", fps_set)
    width = round(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = round(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print("Width:", width, "Height:", height)
    video = cv2.VideoWriter(filename=save_dir + video_out_name,
                            fourcc=cv2.VideoWriter_fourcc(*'mp4v'),
                            fps=fps_set,
                            frameSize=(width, height))
    frameno = 0
    success, frame = cap.read()
    pbar = tqdm(total=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
    while success:
        img = frame
        pbar.update(frameno)
        if frameno in msx.keys():
            for n in range(len(msx[frameno][1])):
                tr_id = int(msx[frameno][0][n].item())
                cat = int(tr_info[1, tr_id].item()) - 1
                if conf_filter is not None:
                    if tr_info[2, tr_id].item() < conf_filter:
                        continue
                if with_ID:
                    a_id = int(tr_info[0, tr_id].item())
                if with_location and len(msx[frameno]) > 3 and len(msx[frameno][3]) > n:
                    loc = msx[frameno][4][n]
                coords = (msx[frameno][1][n]).astype(int)

                if len(coords) == 0:  # empty detection segment
                    continue
                bbox = [min(coords[:, 0]), min(coords[:, 1]), max(coords[:, 0]), max(coords[:, 1])]

                img = cv2.polylines(img, [coords], True, cat_conv_col[cat], thickness=cat + 1)
                img = cv2.putText(img, str(tr_id), (int(bbox[0]), int(bbox[3])), cv2.FONT_HERSHEY_SIMPLEX, 1,
                                  cat_conv_col[cat], 2)
                if cat == 0:
                    img = cv2.rectangle(img, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])),
                                        cat_conv_col[cat], thickness=1)
                    if with_ID:
                        img = cv2.putText(img, a_id_conv[a_id], (int(bbox[0]), int(bbox[1])), cv2.FONT_HERSHEY_SIMPLEX,
                                          1, cat_conv_col[cat], 2)
                    if with_location and len(msx[frameno]) > 3 and len(msx[frameno][3]) > n:
                        img = cv2.putText(img, loc, (int(bbox[0]), int(bbox[1])+20), cv2.FONT_HERSHEY_SIMPLEX,
                                          1, (0, 238, 238), 2)
        video.write(img)
        frameno += 1
        success, frame = cap.read()
    cap.release()
    pbar.close()
    video.release()
    print("Created - ", video_out_name)
    return
