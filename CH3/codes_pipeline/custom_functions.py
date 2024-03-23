import pandas as pd
import torch
from torchvision.ops import box_iou

import time
import json
from datetime import datetime
from shapely import Polygon, Point
from itertools import compress
import numpy as np
import pickle



def first_estimation_tensor(fw_id, wide_tr_tensor, wide_match_tensor, tr_cls, tr_len, tr_conf, tr_id):
    """
    Function to identify individuals based on presence of HP (overlap with two other classes)
    """
    for tid in range(fw_id.shape[1]):
        if wide_tr_tensor[:, tid, 1:].squeeze().dim() == 0:
            tr_cls[tid] = wide_tr_tensor[:, tid, 1:].squeeze() + 1
            tr_len[tid] = len(wide_match_tensor[:, tid, 0].nonzero())
        elif torch.bincount(wide_tr_tensor[:, tid, 1:].squeeze())[1:].nelement() != 0:
            tr_cls[tid] = torch.argmax(torch.bincount(wide_tr_tensor[:, tid, 1:].squeeze())[1:]) + 1
            tr_len[tid] = len(wide_match_tensor[:, tid, 0].nonzero())

        if torch.bincount(fw_id[:, tid])[1:].nelement() != 0:
            tr_len[tid] = len(wide_match_tensor[:, tid, 0].nonzero())
            # calculates confidence based on the count of the most predicted identity on track divided by length of
            # the track
            tr_conf[tid] = torch.max(torch.bincount(fw_id[:, tid])[1:]) / tr_len[
                tid]
            if tr_conf[tid] < 0.3:
                tr_id[tid] = torch.zeros(1)
            else:
                tr_id[tid] = torch.argmax(torch.bincount(fw_id[:, tid])[1:]) + 1
    # saving into one tensor
    return torch.stack([tr_id, tr_cls, tr_conf, tr_len])


def second_estimation(tr_info, wide_match_tensor):
    """
    Function to identify most common id for a track number
    """
    for tid in range(1, tr_info.shape[1]):
        # find trackids that are a best match with current track
        rnr_matched_ids = torch.unique(wide_match_tensor[:, tid, 1:].reshape(-1))
        # get track info of current track and matched tracks
        rnr_trinf_matched = torch.cat((tr_info[:, tid].reshape(4, 1), tr_info[:, rnr_matched_ids]), 1)
        # count animal id occurences over all overlapping tracks
        rnr_unique_labels, rnr_labels_count = rnr_trinf_matched[0, :].unique(return_counts=True)
        #create empty tensors
        rnr_idsumconfs = torch.zeros(int(max(rnr_unique_labels)) + 1)
        rnr_idcounts = torch.zeros(int(max(rnr_unique_labels)) + 1)
        # "normalise" confidence to 105 detections (length of track needs to be 105 or a penalty is applied)
        rnr_trinf_matched[3, :] = rnr_trinf_matched[3, :] / 105
        rnr_trinf_matched[3, rnr_trinf_matched[3, :] > 1] = 1
        rnr_idsumconfs = rnr_idsumconfs.index_add(0, rnr_trinf_matched[0, :].to(torch.int64),
                                                  rnr_trinf_matched[2, :] *
                                                  rnr_trinf_matched[3, :])
        rnr_idcounts = rnr_idcounts.index_add(0, rnr_unique_labels.to(torch.int64),
                                              rnr_labels_count.to(torch.float))
        rnr_cmn_id = torch.argmax(torch.nan_to_num(rnr_idsumconfs / rnr_idcounts))
        if tr_info[0, tid] != rnr_cmn_id:
            tr_info[0, tid] = rnr_cmn_id
            tr_info[2, tid] = torch.max(torch.nan_to_num(rnr_idsumconfs / rnr_idcounts))
    return tr_info


def third_estimation(tr_info, wide_tr_tensor):
    """
    Function to identify tracks that exist simultaneoulsy (on same frame) and sort identity to most likely track
    """
    for tid in range(0, tr_info.shape[1]):
        # for track check which tracks exist in same frames
        rnr_exist_simult = torch.sum((wide_tr_tensor[:, :, 0] != 0).to(torch.int64).add(
            (wide_tr_tensor[:, tid, 0] != 0).to(torch.int64).unsqueeze(1)) > 1, dim=0).nonzero().squeeze()
        rnr_exist_simult = rnr_exist_simult[rnr_exist_simult != tid]
        rnr_trinf_matched = tr_info[:, rnr_exist_simult]
        # use length of track as weight len/total num frames
        rnr_trinf_matched[3, :] = rnr_trinf_matched[3, :] / wide_tr_tensor.shape[0]
        rnr_old_tr_info = tr_info[:, tid]
        # check if multiple predictions exist - each ID-Part should exist only once
        if rnr_exist_simult.nelement() != 0 and True in [torch.equal(rnr_trinf_matched[:2, i], tr_info[:2, tid]) for
                                                         i in range(rnr_exist_simult.nelement())]:
            rnr_idxs = torch.Tensor([i for i in range(rnr_trinf_matched.shape[1]) if
                                     torch.equal(rnr_trinf_matched[:2, i], tr_info[:2, tid])]).to(torch.int64)
            # if match with higher conf
            if torch.max(rnr_trinf_matched[2, rnr_idxs] * rnr_trinf_matched[3, rnr_idxs]) > \
                    tr_info[2, tid] * tr_info[3, tid] / wide_tr_tensor.shape[0]:
                # if match with old id - test higher conf score -test if should stay old or be unsure
                if True in [torch.equal(rnr_trinf_matched[:2, i], rnr_old_tr_info[:2]) for i in
                            range(rnr_trinf_matched.shape[1])]:
                    rnr_idxs_old = torch.Tensor([i for i in range(rnr_trinf_matched.shape[1]) if
                                                 torch.equal(rnr_trinf_matched[:2, i], rnr_old_tr_info[:2])]).to(
                        torch.int64)
                    # if other conf bigger set unsure
                    if torch.max(rnr_trinf_matched[2, rnr_idxs_old] * rnr_trinf_matched[3, rnr_idxs_old]) > \
                            rnr_old_tr_info[2] * rnr_old_tr_info[3] / wide_tr_tensor.shape[0]:
                        tr_info[0, tid] = 0
                        tr_info[2, tid] = 0.
                    # otherwise change back to old
                    else:
                        tr_info[0, tid] = rnr_old_tr_info[0]
                        tr_info[2, tid] = rnr_old_tr_info[2]
                        # print("pos1:::")#, "curr:", tid, "comp:", rnr_matched_ids[
                        # rnr_idxs_old])  # test if needed - if tid > than compared ids can have double detections again
            # other conf smaller keep new id
            else:
                # change previous track ids to unsure
                rnr_i = [rnr_exist_simult[rxi] for rxi in rnr_idxs if rnr_exist_simult[rxi] > tid]
                if len(rnr_i) == 0:  # if bigger will be addressed in for loop
                    continue
                else:
                    # print("pos2:::")#, "curr:", tid, "comp:", rnr_idxs, rnr_matched_ids)
                    tr_info[0, rnr_i] = 0
                    tr_info[2, rnr_i] = 0.
    return tr_info


def last_estimation(tr_info, wide_tr_tensor):
    """
    Function to check for unidentified tracks and see if it occurs alone with an identified track -
    will take the alternative identitiy
    """
    for tid in range(0, tr_info.shape[1]):
        # already has a valid ID
        if tr_info[0, tid] > 0 and tr_info[0, tid] < 3:
            continue
        # for track check which tracks exist in same frames
        rnr_exist_simult = torch.sum((wide_tr_tensor[:, :, 0] != 0).to(torch.int64).add(
            (wide_tr_tensor[:, tid, 0] != 0).to(torch.int64).unsqueeze(1)) > 1, dim=0).nonzero().squeeze()
        rnr_exist_simult = rnr_exist_simult[rnr_exist_simult != tid]
        if rnr_exist_simult.nelement() != 0:
            rnr_trinf_matched_cl = tr_info[:, rnr_exist_simult[tr_info[1, tid] == tr_info[1, rnr_exist_simult]]]
            rnr_clsids_exist = [t.to(torch.int64) for t in rnr_trinf_matched_cl[0, :]]
            if 1 not in rnr_clsids_exist or 2 not in rnr_clsids_exist:
                if 1 in rnr_clsids_exist:
                    tr_info[0, tid] = 2
                elif 2 in rnr_clsids_exist:
                    tr_info[0, tid] = 1
    return tr_info


def predict_id_hp_location_hardcoded(res, vid_path):
    """
    Function to match boxes of different classes together to identify animals with and without HP
    :param
    res: results from model.track prediction using yolov8 segmentation (can be stream)
    vid_path: path to video
    :hidden:
            match_tensor: tensor[Frame_Number, Track_ID, MaskNumber (Index + 1), best match body*, best match head*, best match headpiece*] *(track_id of overlapping box on that frame)
            tr_tensor: tensor[Frame_Number, Track_ID, MaskNumber, Class]
    :return:
    msk_dict: dict{Frame_Number}[Track_IDs, [mask segments]]
    tr_info: tensor[tr_A-id/tr_cl/tr_conf, tr_id] conf here is number of frames where overlap with HP or not divided by all detections of track
    """
    match_ls = []
    tr_ls = []
    msk_dict = {}
    ri = 0
    timestart = time.time()
    loc_dict = find_hardcoded_location_map_by_date(vid_path)
    if loc_dict is None:
        print("No hardcoded locations found - ", vid_path.split("/")[-1])
    for frame_res in res:
        # frame_res = res[ri]
        # if no detections continue
        if frame_res.boxes.cls.nelement() == 0:
            ri += 1
            continue
        # calculating max values, indices for box overlaps excluding self and only matching with specific class
        match_bds = torch.max(
            box_iou(frame_res.boxes.xyxy, frame_res.boxes.xyxy).fill_diagonal_(0) *
            (frame_res.boxes.cls == 0),
            dim=1)
        match_hds = torch.max(
            box_iou(frame_res.boxes.xyxy, frame_res.boxes.xyxy).fill_diagonal_(0) *
            (frame_res.boxes.cls == 1),
            dim=1)
        match_hps = torch.max(
            box_iou(frame_res.boxes.xyxy, frame_res.boxes.xyxy).fill_diagonal_(0) *
            (frame_res.boxes.cls == 2),
            dim=1)
        # detection not tracked only one detection
        if frame_res.boxes.id is None and len(frame_res.boxes) == 1:
            id = torch.tensor([0.])
            tr_ls.append(torch.stack((torch.full(id.shape, ri), id, torch.arange(len(frame_res.boxes)) + 1,
                                      frame_res.boxes.cls.cpu() + 1), -1))
            msk_dict[ri] = [id, frame_res.masks.xy]
            ri += 1
            continue
        # detection not tracked multiple detections
        elif frame_res.boxes.id is None:
            id = torch.zeros(len(frame_res.boxes))
        # detections are tracked - add track ids
        else:
            id = frame_res.boxes.id
        # calculate best match for given Part
        bm_bd = id[match_bds.indices.cpu()] * (match_bds.values != 0).cpu()
        bm_hd = id[match_hds.indices.cpu()] * (match_hds.values != 0).cpu()
        bm_hp = id[match_hps.indices.cpu()] * (match_hps.values != 0).cpu()
        # reshaping and stacking
        mat = torch.stack((torch.full(id.shape, ri), id, torch.arange(len(frame_res.boxes)) + 1, bm_bd, bm_hd, bm_hp),
                          -1)
        match_ls.append(mat)
        tr_ls.append(torch.stack((torch.full(id.shape, ri), id, torch.arange(len(frame_res.boxes)) + 1,
                                  frame_res.boxes.cls.cpu() + 1), -1))
        # if location map present make predictions
        if loc_dict is not None:
            centroids = [Polygon(p).centroid if len(p) > 4 else Point(np.mean(p, axis=0)) for p in frame_res.masks.xy]
            areas = [Polygon(p).area if len(p) > 4 else np.nan for p in frame_res.masks.xy]
            msk_dict[ri] = [id, frame_res.masks.xy, centroids, areas,
                            predict_locations_hardcoded([id, frame_res.masks.xy,
                                                         centroids], loc_dict)]
        else:
            msk_dict[ri] = [id, frame_res.masks.xy,
                            [Polygon(p).centroid if len(p) > 4 else Point(np.mean(p, axis=0)) for p in
                             frame_res.masks.xy],
                            [Polygon(p).area if len(p) > 4 else np.nan for p in frame_res.masks.xy]]
        ri += 1
    print(f"Time running YOLOv8: {time.time() - timestart}.")
    rnr_time = time.time()
    if len(match_ls) == 0 and len(tr_ls) == 0:
        print("No detections...")
        return [], {}
    elif len(match_ls) == 0:
        print("macth_ls is empty")
    elif len(tr_ls) == 0:
        print("tr_ls is empty")
    else:
        tr_tensor = torch.cat(tr_ls)
        match_tensor = torch.cat(match_ls)
        # widening the tensor [Frame_Number, Track_ID, Mask_Number, BMs (BM-BD), (BM-HD), (BM-HP)]
        wide_match_tensor = torch.zeros(int(max(match_tensor[:, 0]).item() + 1),
                                        int(max(match_tensor[:, 1] + 1).item()), 4)
        wide_match_tensor = torch.index_put(wide_match_tensor,
                                            (match_tensor[:, 0].to(torch.int64), match_tensor[:, 1].to(torch.int64)),
                                            match_tensor[:, 2:]).to(torch.int64)

        # widening the tensor [Frame_Number, Track_ID, CLs]
        wide_tr_tensor = torch.zeros(int(max(tr_tensor[:, 0]).item() + 1), int(max(tr_tensor[:, 1] + 1).item()), 2)
        wide_tr_tensor = torch.index_put(wide_tr_tensor,
                                         (tr_tensor[:, 0].to(torch.int64), tr_tensor[:, 1].to(torch.int64)),
                                         tr_tensor[:, 2:]).to(torch.int64)

        # summing up if matches with bd, hd or hp -> 2 if hp 1 if no hp -> tensor size (frame number, num track-ids) - could be 3 when close to same cls detection
        fw_id = torch.sum(wide_match_tensor[:, :, 1:] != 0, dim=2)
        tr_cls = torch.zeros(fw_id.shape[1])
        tr_id = torch.zeros(fw_id.shape[1])
        tr_conf = torch.zeros(fw_id.shape[1])
        tr_len = torch.zeros(fw_id.shape[1])
        tr_info = first_estimation_tensor(fw_id, wide_tr_tensor, wide_match_tensor, tr_cls,
                                          tr_id,
                                          tr_conf,
                                          tr_len)
        # tr_info = torch.from_numpy(first_estimation_tensor(fw_id.detach().cpu().numpy(),
        #                                                    wide_tr_tensor.detach().cpu().numpy(),
        #                                                    wide_match_tensor.detach().cpu().numpy()))
        print(f"Time running first estimation: {time.time() - rnr_time}.")
        rnr_time = time.time()
        # adding second estimation - using cls and confidence of all overlapping masks
        # take average of conf scores for each id over masks - max is reassigned
        tr_info = second_estimation(tr_info, wide_match_tensor)
        print(f"Time running second estimation: {time.time() - rnr_time}.")
        rnr_time = time.time()

        tr_info = third_estimation(tr_info, wide_tr_tensor)
        print(f"Time running third estimation: {time.time() - rnr_time}.")
        rnr_time = time.time()

        # if one ID already there must be the other
        tr_info = last_estimation(tr_info, wide_tr_tensor)
        print(f"Time running last estimation: {time.time() - rnr_time}.")

        print(f"Total time for video: {time.time() - timestart}.")
        return tr_info, msk_dict


def convert_vidpath2datetime(vid_path):
    """
    Function converts video path to date (expects format "camMod"_Date_Time...)
    :param
    vid_path: path to video
    :return:
    vid_date: datetime object - date and time of video
    """
    if vid_path.split("/")[-1].split("_")[0] == "Test":
        vid_date = datetime.strptime("-".join(vid_path.split("/")[-1].split(".")[0].split("_")[1:3]), '%Y%m%d-%H%M%S')
    else:
        vid_date = datetime.strptime("-".join(vid_path.split("/")[-1].split(".")[0].split("_")[2:4]), '%Y%m%d-%H%M%S')
    return vid_date


def find_hardcoded_location_map_by_date(vid_path):
    """
    Function converts video path to date (expects format "camMod"_Date_Time...)
    :param
    vid_path: path to video
    :return:
    loc_dict: dictionary - json labels for matching date location map
    """
    cammod = vid_path.split("/")[-1].split("_")[0]
    if cammod == "Test":
        cammod = "1"
    elif cammod == "CamMod":
        cammod = vid_path.split("/")[-1].split("_")[1]
    camera = vid_path.split("/")[-1].split("_")[-1].split(".")[0]
    loc_path = "./loc_maps/CamMod_" + cammod + "_location_hc_json.json"
    loc_map = json.load(open(loc_path))
    n_keys = [datetime.strptime("-".join(k.split("_")[4:]).split(".")[0], '%Y%m%d-%H%M%S')
              for k in loc_map.keys() if camera in k]
    loc_dict = dict(zip(n_keys, list(loc_map.values())))
    vid_date = convert_vidpath2datetime(vid_path)
    if len([k for k in n_keys if k > vid_date]) == 0:
        print("No hc_loc_map")
        return None
    else:
        print("loc_map: ", loc_dict[min([k for k in n_keys if k > vid_date])]['filename'])
        return loc_dict[min([k for k in n_keys if k > vid_date])]


def predict_locations_hardcoded(mask, loc_dict):
    """
    Function predicts location based on centroid of mask and hard coded polygons using shapely
    :param
    mask: entry of mask dict: [tensor[tr_id], list[masks - np.ndarrays], list[centroids - shapely.Points]
    loc_dict: location dictionary read with find_hardcoded_location_map_by_date
    :return:
    pred: list of predictions
    """
    loc_polygons = [Polygon(zip(r['shape_attributes']['all_points_x'], r['shape_attributes']['all_points_y'])) for r in
                    loc_dict['regions']]
    loc_labels = [r['region_attributes']['location'] for r in loc_dict['regions']]
    pred = [l[0] if l else 'other' for l in
            [list(compress(loc_labels, [p.contains(point) for p in loc_polygons])) for point in mask[2]]]
    # sum([list(compress(loc_labels, [p.contains(point) for p in loc_polygons])) for point in mask[2]], [])
    return pred


def convert_pkl2dataframe(pkl_path):
    with open(pkl_path, "rb") as f:
        tr_info, msx = pickle.load(f)
    df = convert_objcts2dataframe(tr_info, msx)
    df['file_name'] = pkl_path.split("/")[-1].split(".")[0]
    return df


def convert_objcts2dataframe(tr_info, msx):
    df = pd.DataFrame([{'frame_number': k, 'track_id': int(msx[k][0][r]),
                        'animal_id': tr_info[0, int(msx[k][0][r])].item(),
                        'seg_class': tr_info[1, int(msx[k][0][r])].item(),
                        'track_conf': tr_info[2, int(msx[k][0][r])].item(),
                        'poly_area': msx[k][3][r],
                        'location': msx[k][4][r] if len(msx[k]) > 4 else np.nan,
                        'x': int(msx[k][2][r].x) if not msx[k][2][r].is_empty else np.nan,
                        'y': int(msx[k][2][r].y) if not msx[k][2][r].is_empty else np.nan}
                       for k in msx.keys() for r in range(len(msx[k][0])) if int(msx[k][0][r]) != 0])
    return df
