# Codes for Pipeline

## batch_analyse.py
This code runs the pipeline and analyses videos from a directory. Multiple instances of this code can be run to analyse videos in parallel but keep an eye on GPU/CPU ussage to not crash running instances.

## csv_file_analysis.py
Code to be run on output of pipeline to dwon sample detections to .5 Hz frequency for easier analysis - outut of right and left camera can be matched to achieve higher prediciton accuracy

## custom_functions.py
Code holding the main functions used in batch_analyse.py - such as the functions to identify animal based on overlap with other detection classes and track matching of identities

## custom_plot_functions.py
Code to plot predictions into a video file

## yolov8_CBC-segmodel.pt
YOLOv8 weights for model

## custom_CBC.yaml
example for .yaml file used for YOLOv8 model

## custom_tracker_bots.yaml
.yaml file for input to use botsort tracking algorithm in YOLOv8 model
