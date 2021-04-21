import os
import pydicom
from pydicom.errors import InvalidDicomError
# import gdcm
import numpy
import time
from pydicom import dcmread
import matplotlib
matplotlib.use('pdf')
import matplotlib.pyplot as plt


def writeImage(id, image):
    path = str(id) + '.jpg'
    if len(image.shape) > 3:
        pic_num = image.shape[0]
        height = int(pic_num ** 0.5)
        width = int(pic_num / height)
        if height * width < pic_num:
            width += 1
        f= plt.figure(figsize=(width*6.4, (4.8/6.4)*(width*6.4)),clear = True, dpi=300)
        
        plt.xticks([]),plt.yticks([])
        for i in range(image.shape[0]):
            f.add_subplot(width, height, i + 1)
            plt.xticks([]), plt.yticks([])
            plt.imshow(image[i], cmap = plt.cm.bone)
        plt.subplots_adjust(wspace=0, hspace =0)
        plt.savefig(os.path.join('upload', path), bbox_inches='tight',dpi=300)
    else:
        f = plt.figure(clear = True)
        plt.xticks([]),plt.yticks([])
        plt.imshow(image, cmap=plt.cm.bone)
        plt.savefig(os.path.join('upload', path), bbox_inches='tight', dpi = 300)
    return path

def readDcm(filename, number):
    # Dcm 文件读取
    ds = None
    try:
    
    
        ds = pydicom.dcmread(filename)  # plan dataset
    except InvalidDicomError:
        pass
        
    
    if hasattr(ds,'PixelData'):
        writeImage(number, ds.pixel_array)
        pass

# from pydicom.data import get_testdata_files

def prase(path, number):
    c = number
    if os.path.isdir(path):
        for p in os.listdir(path):
            c = prase(os.path.join(path, p), c)
    else:
        readDcm(path, c)
        c += 1
    return c
        # print(path)
# global number

number = 1
from PIL import Image

def transfer(path):
    if os.path.isdir(path):
        for p in os.listdir(path):
            c = transfer(os.path.join(path, p))
    else:
        filename = os.path.basename(path)
        filename = filename[0:filename.find('.')] + '.jpg'
        image = Image.open(path)
        image = image.convert("RGB")
        image.save(os.path.join('medical_instance\\upload',filename))

if __name__ == "__main__":
    transfer('medical_instance\\1uo')
    # prase('HL7Test', 1)
#     # readDcm(get_testdata_files("CT_small.dcm")[0])
#     prase('pcap/1590114835/DICOM|http/Y_1590114897.1665974_10.246.229.255-8080_10.245.145.250-50577.unknow')
