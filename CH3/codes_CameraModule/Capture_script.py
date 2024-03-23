#!/usr/bin/python2.7

from time import sleep
from pijuice import PiJuice
import arducam_mipicamera as arducam
import time
import os
import datetime
import RPi.GPIO as GPIO
import subprocess
import v4l2 #sudo pip install v4l2
import time
import ctypes
import numpy as np

# Define variables
AvailSpace = True
vid_count = 0
usb = "A"
#will close B so open B
os.system("sudo mount /dev/sdb1 /mnt/usbB -o uid=pi,gid=pi")
save_dir = '/mnt/usbB/'
vidlen=600 #length of vid in seconds

usbA_notfull = True
usbB_notfull = True

pijuice = PiJuice(1, 0x14)
print(pijuice.status.GetStatus())

if __name__ == "__main__":
    try:
        camera = arducam.mipi_camera()
        print("Open camera...")
        camera.init_camera()
        print("Setting the resolution...")
        camera.set_mode(8)
        fmt = camera.get_format()
        print("Current resolution is {} x {}".format(fmt['width'],fmt['height']))

        # start preview and blink LED to indicate script is starting
        print("Start preview...")
        camera.start_preview(fullscreen = False, window = (0, 0, 2560, 720))
        set_controls(camera)
        pijuice.status.SetLedBlink('D2', 1,[255, 0, 0], 500, [0, 255, 0], 500)
        sleep(1)
        pijuice.status.SetLedBlink('D2', 1,[0, 0, 255], 500, [200, 200, 200], 500)
        sleep(1)
        pijuice.status.SetLedBlink('D2', 1,[255, 0, 0], 500, [0, 255, 0], 500)
        sleep(1)
        pijuice.status.SetLedBlink('D2', 1,[0, 0, 255], 500, [0, 0, 0], 500)
        sleep(1)

        start_time = datetime.datetime.now()
        AvailSpace = True
        print("Start Time:")
        print(start_time.strftime("%Y %m %d_%H:%M:%S"))
        

        while ((AvailSpace)):
            log = open("/home/pi/Desktop/logfile.txt",'a')
            # script will change between USB drives
            if usb == "A":
                #Unmount B (when changed to it) - added a break of 1 vid (target still busy)
                if vid_count == 1:
                    #check available space on diskB:
                    disk = os.statvfs(save_dir)
                    totalAvailSpaceNonRoot = float(disk.f_bsize * disk.f_bavail) / 1024 / 1024 / 1024
                    if totalAvailSpaceNonRoot < 25:
                        msg_SpaceB ="\nUSB-B Status messsage\n\nStorage left: "+str(totalAvailSpaceNonRoot)
                        send_email(msg_SpaceB)
                        if totalAvailSpaceNonRoot <3:
                            usbB_notfull=False
                    else:
                        usbB_notfull=True                
                    os.system("sudo umount /mnt/usbB")
                #Mount A (when changed to it)
                if vid_count ==0:
                    save_dir = '/mnt/usbA/'
                    os.system("sudo mount /dev/sda1 /mnt/usbA -o uid=pi,gid=pi")
                    logA = open("/mnt/usbA/logBKUP.txt",'a')
                    #Catch if USB not present
                    if os.listdir(save_dir)==[]:
                        print("USB-A not mounted!")
                        usb = "B"
                        continue
                    else:
                        print(save_dir)
                #LED-usb Blue==1 Green==2
                if vid_count == 0:
                    pijuice.status.SetLedState('D2', [122,0,122])
                elif "usb1.txt" in os.listdir(save_dir):
                    pijuice.status.SetLedState('D2', [0,0,120])
                elif "usb2.txt" in os.listdir(save_dir):
                    pijuice.status.SetLedState('D2', [0,120,0])
                else:
                    pijuice.status.SetLedState('D2', [120,0,0])
            elif usb == "B":
                #Unmount A (when newly changed to it)
                if vid_count == 1:
                    #check available space on diskA:
                    disk = os.statvfs(save_dir)
                    totalAvailSpaceNonRoot = float(disk.f_bsize * disk.f_bavail) / 1024 / 1024 / 1024
                    if totalAvailSpaceNonRoot < 25:
                        msg_SpaceA ="\nUSB-A Status messsage\n\nStorage left: "+str(totalAvailSpaceNonRoot)
                        send_email(msg_SpaceA)
                        if totalAvailSpaceNonRoot <3:
                            usbA_notfull=False
                    else:
                        usbA_notfull=True
                    os.system("sudo umount /mnt/usbA")
                #Mount usb B (when changed to it)
                if vid_count ==0:
                    save_dir = '/mnt/usbB/'
                    os.system("sudo mount /dev/sdb1 /mnt/usbB -o uid=pi,gid=pi")
                    logB = open("/mnt/usbB/logBKUP.txt",'a')
                    #Catch if USB not present
                    if os.listdir(save_dir)==[]:
                        print("USB-B not mounted!")
                        usb = "A"
                        continue
                    else:
                        print(save_dir)
                #LED-usb Blue==1 Green==2
                if vid_count == 0:
                    pijuice.status.SetLedState('D2', [122,0,122])
                elif "usb1.txt" in os.listdir(save_dir):
                    pijuice.status.SetLedState('D2', [0,0,120])
                elif "usb2.txt" in os.listdir(save_dir):
                    pijuice.status.SetLedState('D2', [0,120,0])
                else:
                    pijuice.status.SetLedState('D2', [120,0,0])
                
            #Capture - this part records the actual video
            log_ls = []
            start_time = datetime.datetime.now()
            fileName = "%s/%s_%s.h264" % (save_dir, 'Test', start_time.strftime("%Y%m%d_%H%M%S"))
            log_ls.append(fileName)
            file = open(fileName, "wb")
            # Need keep py_object reference
            file_obj = ctypes.py_object(file)
            print(file_obj)
            camera.set_video_callback(callback, file_obj)
            time.sleep(vidlen)
            now_time = time.time()
            camera.set_video_callback(None, None)
            
            #Check Battery
            log_ls.append(str(pijuice.status.GetStatus()['data']['battery']))
            
            
            
            #check battery input:
            if (pijuice.status.GetStatus()['data']['battery'] != 'CHARGING_FROM_IN'):
                msg_bat =("\nRaspberry Pi Status messsage\n\nBattery: "+str(pijuice.status.GetStatus()['data']['battery']))
                send_email(msg_bat)
            
            #Check space & change disk
            disk = os.statvfs(save_dir)
            totalAvailSpaceNonRoot = float(disk.f_bsize * disk.f_bavail) / 1024 / 1024 / 1024
            log_ls.append("   "+"using USB"+usb+" -- "+str(totalAvailSpaceNonRoot))
            log_ls.append("----\n")
            
            #write in LogFile
            print(log_ls)
            log.write("\n".join([x for x in log_ls]))
            if usb == "A":
                logA.write("\n".join([x for x in log_ls]))
            elif usb == "B":
                logB.write("\n".join([x for x in log_ls]))
            #change USB every 5 videos change to other USB
            if vid_count>=4:
                log.close()
                if usb == "A":
                    logA.close()
                    if usbB_notfull:
                        print("change to USB - B")
                        usb = "B"
                        vid_count=0
                    else:
                        print("keep USB - A !!B FULL!!")
                        if totalAvailSpaceNonRoot <3:
                            AvailSpace = False
                        vid_count=0        
                elif usb == "B":
                    logB.close()
                    if usbA_notfull:
                        print("change to USB - A")
                        usb = "A"
                        vid_count=0
                    else:
                        print("keep USB - B !!A FULL!!")
                        if totalAvailSpaceNonRoot <3:
                            AvailSpace = False
                        vid_count=0
            else:
                vid_count +=1
        file.close()
        pijuice.status.SetLedState('D2', [0,0,0])
        print("Stop preview...")
        camera.stop_preview()
        print("Close camera...")
        camera.close_camera()
    except Exception as e:
        print(e)
