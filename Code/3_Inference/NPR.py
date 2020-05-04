# -*- coding: utf-8 -*-
"""
Created on Sun Dec 22 00:25:00 2019

@author: Nirmal
"""

import os
import sys

import cv2
import numpy as np
import copy 
import pytesseract

#pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def ocr(img_path,xmin, ymin, xmax, ymax):
    
    im = cv2.imread(img_path)
    
#    mask = np.full(im.shape[:2], 0, dtype=np.uint8)
    image = copy.copy(im)
    
#    temp = cv2.bitwise_and(image,image,mask = mask)
    temp = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    Cropped = temp[ymin:ymax, xmin:xmax]
    
#    cv2.imwrite('aa.jpg', temp)
#    cv2.imshow("Image", temp)

    #Read the number plate
    text = pytesseract.image_to_string(Cropped)
    print("Detected Number is:",text)
    
    cv2.rectangle(image, (xmin, ymin), (xmax, ymax), (0, 255, 0),1)
    cv2.putText(image,text,(xmin, ymax+15),cv2.FONT_HERSHEY_COMPLEX,0.5,(0,255,0),1)
    cv2.imwrite("../../Predicted output.jpg", image)
    cv2.imshow("Image", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
#    return text

def get_parent_dir(n=1):
    """ returns the n-th parent dicrectory of the current
    working directory """
    current_path = os.path.dirname(os.path.abspath(__file__))
    for k in range(n):
        current_path = os.path.dirname(current_path)
    return current_path

src_path = os.path.join(get_parent_dir(1),'2_Training','src')
utils_path = os.path.join(get_parent_dir(1),'Utils')

sys.path.append(src_path)
sys.path.append(utils_path)

import argparse
from keras_yolo3.yolo import YOLO, detect_video
from PIL import Image
from timeit import default_timer as timer
from utils import load_extractor_model, load_features, parse_input, detect_object
import test
import utils
import pandas as pd
import numpy as np
from Get_File_Paths import GetFileList
import random

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

# Set up folder names for default values
data_folder = os.path.join(get_parent_dir(n=1),'Data')

image_folder = os.path.join(data_folder,'Source_Images')

image_test_folder = os.path.join(image_folder,'Test_Images')

detection_results_folder = os.path.join(image_folder,'Test_Image_Detection_Results') 
detection_results_file = os.path.join(detection_results_folder, 'Detection_Results.csv')

model_folder =  os.path.join(data_folder,'Model_Weights')

model_weights = os.path.join(model_folder,'checkpoint.h5')
#model_weights = os.path.join(model_folder,'trained_weights_final.h5')
model_classes = os.path.join(model_folder,'data_classes.txt')

anchors_path = os.path.join(src_path,'keras_yolo3','model_data','yolo_anchors.txt')

FLAGS = None

data = input('Enter the image name for Prediction:')

if __name__ == '__main__':
    # Delete all default flags
    parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
    '''
    Command line options
    '''

#    parser.add_argument(
#        "--input_path", type=str, default=image_test_folder,
#        help = "Path to image/video directory. All subdirectories will be included. Default is " + image_test_folder
#    )

    parser.add_argument(
        "--output", type=str, default=detection_results_folder,
        help = "Output path for detection results. Default is " + detection_results_folder
    )

    parser.add_argument(
        "--no_save_img", default=False, action="store_true",
        help = "Only save bounding box coordinates but do not save output images with annotated boxes. Default is False."
    )

    parser.add_argument(
        "--file_types", '--names-list', nargs='*', default=['.jpg'], 
        help = "Specify list of file types to include. Default is --file_types .jpg .jpeg .png .mp4"
    )

    parser.add_argument(
        '--yolo_model', type=str, dest='model_path', default = model_weights,
        help='Path to pre-trained weight files. Default is ' + model_weights
    )

    parser.add_argument(
        '--anchors', type=str, dest='anchors_path', default = anchors_path,
        help='Path to YOLO anchors. Default is '+ anchors_path
    )

    parser.add_argument(
        '--classes', type=str, dest='classes_path', default = model_classes,
        help='Path to YOLO class specifications. Default is ' + model_classes
    )

    parser.add_argument(
        '--gpu_num', type=int, default = 1,
        help='Number of GPU to use. Default is 1'
    )

    parser.add_argument(
        '--confidence', type=float, dest = 'score', default = 0.10,
        help='Threshold for YOLO object confidence score to show predictions. Default is 0.25.'
    )


    parser.add_argument(
        '--box_file', type=str, dest = 'box', default = detection_results_file,
        help='File to save bounding box results to. Default is ' + detection_results_file
    )
    
#    parser.add_argument(
#        '--postfix', type=str, dest = 'postfix', default = '_catface',
#        help='Specify the postfix for images with bounding boxes. Default is "_catface"'
#    )
    

    FLAGS = parser.parse_args()

    save_img = not FLAGS.no_save_img

    file_types = FLAGS.file_types

#    if file_types:
#        input_paths = GetFileList(FLAGS.input_path, endings = file_types)
#    else:
#        input_paths = GetFileList(FLAGS.input_path)

    #Split images and videos
    img_endings = ('.jpg')
#    input_paths='C:/Users/Nirmal/Documents/Velodyne/try1/TrainYourOwnYOLO/Data/Source_Images/Test_Images'
    input_paths=os.path.join(get_parent_dir(1),'Data','Source_Images','Test_Images')
    
    img_path=os.path.join(get_parent_dir(1),'Data','Source_Images','Test_Images',data)
    input_image_paths = [] 
    for item in input_paths:
        if item.endswith(img_endings):
            input_image_paths.append(item)

    output_path = FLAGS.output
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # define YOLO detector
    yolo = YOLO(**{"model_path": FLAGS.model_path,
                "anchors_path": FLAGS.anchors_path,
                "classes_path": FLAGS.classes_path,
                "score" : FLAGS.score,
                "gpu_num" : FLAGS.gpu_num,
                "model_image_size" : (416, 416),
                }
               )

    # Make a dataframe for the prediction outputs
    out_df = pd.DataFrame(columns=['image', 'image_path','xmin', 'ymin', 'xmax', 'ymax', 'label','confidence','x_size','y_size'])

    # labels to draw on images
    class_file = open(FLAGS.classes_path, 'r')
    input_labels = ['plate']
    print('Found {} input labels: {} ...'.format(len(input_labels), input_labels))
    
    text_out = ''

    print(img_path)
    prediction, image = detect_object(yolo, img_path, save_img = save_img,
                                      save_img_path = FLAGS.output,)
#                                      postfix=FLAGS.postfix)
    y_size,x_size,_ = np.array(image).shape
    for single_prediction in prediction:
        out_df=out_df.append(pd.DataFrame([[os.path.basename(img_path.rstrip('\n')),img_path.rstrip('\n')]+single_prediction + [x_size,y_size]],columns=['image','image_path', 'xmin', 'ymin', 'xmax', 'ymax', 'label','confidence','x_size','y_size']))
        xmin,ymin,xmax,ymax = single_prediction[0], single_prediction[1], single_prediction[2], single_prediction[3]
        print(img_path, xmin, ymin, xmax, ymax)
        text = ocr(img_path,xmin, ymin, xmax, ymax)

    out_df.to_csv(FLAGS.box,index=False)

    # Close the current yolo session
    yolo.close_session()



