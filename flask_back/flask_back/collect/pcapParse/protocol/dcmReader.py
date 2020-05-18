import os
import pydicom
from pydicom.errors import InvalidDicomError
from database.tables import PatientInfo, StudyInfo, SeriesInfo, ImageInfo, DBSession
# import gdcm
import numpy
import time
from pydicom import dcmread
import matplotlib.pyplot as plt
import scipy.misc

session = DBSession()

map_patient = {
    'PatientName':'patient_name',
    'PatientSex':'patient_sex',
    'PatientBirthDate':'patient_birth_date',
    'PatientBirthTime':'patient_birth_time',
    'PatientWeight':'patient_weight',
    'PatientID':'patient_id',
    'PatientAge':'patient_age',
    'PregnancyStatus':'patient_pregnancy_status'
}
map_image = {
    'SopInstanceUID':'sop_instance_id',
    'ImageDate':'image_date',
    'ImageTime':'image_time',
    'WindowCenter':'window_center',
    'WindowWidth':'window_width'
}
map_study = {
    'AccessionNumber':'study_ris_id',
    'StudyID':'study_id',
    'StudyInstanceUID':'study_instance_id',
    'StudyDate':'study_date',
    'StudyTime':'study_time',
    'BodyPartExamined':'study_body_part',
    'StudyDescription':'study_description',
}
map_series = {
    'SeriesNumber':'series_num',
    'SeriesInstanceUID':'series_instance_id',
    'Modality':'study_modality',
    'SeriesDescription':'series_description',
    'SeriesDate':'series_date',
    'SeriesTime':'series_time'
}
map_type = {
    'PregnancyStatus':int,
    'HighBit':int
}

absPath = 'upload/'

def writeImage(id, image):
    # print(image.shape)
    path = str(id) + '.jpg'
    plt.imshow(image)
    plt.savefig(os.path.join(absPath, path))
    # plt.show()
    # scipy.misc.imsave(os.path.join(absPath, path), image)
    return path

def readDcm(filename):
    # Dcm 文件读取
    ds = None
    try:
        ds = pydicom.dcmread(filename)  # plan dataset
    except InvalidDicomError:
        return
    
    # 患者信息记录
    patient = PatientInfo()
    study = StudyInfo()
    series = SeriesInfo()
    image = ImageInfo()
    patient.send_ip_port = '129.20.2.1:3306'
    patient.receiver_ip_port = '192.2.3.1:3306'
    for i in ds.dir("pat"):
        if i in map_patient.keys():
            if i in map_type.keys():
                patient[map_patient[i]] = map_type[i](ds.data_element(i).value)
            else:
                patient[map_patient[i]] = str(ds.data_element(i).value)

    # 信息记录
    for i in ds.dir("stu"):
        if i in map_study.keys():
            if i in map_type.keys():
                study[map_study[i]] = map_type[i](ds.data_element(i).value)
            else:
                study[map_study[i]] = str(ds.data_element(i).value)
    
    if hasattr(ds,'AccessionNumber'):
        study.study_ris_id = str(ds.AccessionNumber)
    if hasattr(ds,'BodyPartExamined'):
        study.study_body_part = str(ds.BodyPartExamined)
        
    for i in ds.dir("series"):
        if i in map_series.keys():
            if i in map_type.keys():
                series[map_series[i]] = map_type[i](ds.data_element(i).value)
            else:
                series[map_series[i]] = str(ds.data_element(i).value)
    
    if hasattr(ds,'Modality'):
        series.study_modality = str(ds.Modality)
    if hasattr(ds,'SliceThickness'):
        series.slice_thickness = str(ds.SliceThickness)
    if hasattr(ds,'SpacingBetweenSlices'):
        series.spacing_between_slices = str(ds.SpacingBetweenSlices)
    if hasattr(ds,'SliceLocation'):
        series.slice_location = str(ds.SliceLocation)
    
    for i in ds.dir("ima"):
        if i in map_image.keys():
            if i in map_type.keys():
                image[map_image[i]] = map_type[i](ds.data_element(i).value)
            else:
                image[map_image[i]] = str(ds.data_element(i).value)
    if hasattr(ds,'HighBit'):
        image.high_bit = int(ds.HighBit)
    if hasattr(ds,'SopInstanceID'):
        image.sop_instance_id = str(ds.SopInstanceID)
    if hasattr(ds,'WindowCenter'):
        image.window_center = str(ds.WindowCenter)
    if hasattr(ds,'WindowWidth'):
        image.window_width = str(ds.WindowWidth)
    if hasattr(ds,'PixelData'):
        image.image_path = writeImage(patient.id, ds.pixel_array)
        pass

    session.add(patient)
    session.flush()
    study.id = patient.id #改
    series.id = patient.id #改
    image.id = patient.id #改
    
    session.add(series)
    session.add(study)
    session.add(image)
    session.commit()

from pydicom.data import get_testdata_files

def prase(path):
    if os.path.isdir(path):
        for p in os.listdir(path):
            print(p)
            test(os.path.join(path, p))
    else:
        readDcm(path)
        # print(path)

if __name__ == "__main__":
    # readDcm(get_testdata_files("CT_small.dcm")[0])
    prase('DICOM-sample/')
