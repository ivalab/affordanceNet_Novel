#!/usr/bin/env python
"""
See README.md for installation instructions before running.
Demo script to perform affordace detection from images
"""

from os import path
import sys
import time

# Initialize python paths
this_dir = path.dirname(__file__)

# Add caffe to PYTHONPATH
caffe_path = path.join(this_dir, '..', 'caffe-affordance-net', 'python')
if caffe_path not in sys.path:
    sys.path.append(caffe_path)

# Add lib to PYTHONPATH
lib_path = path.join(this_dir, '..', 'lib')
if lib_path not in sys.path:
    sys.path.append(lib_path)

from fast_rcnn.config import cfg
from fast_rcnn.test import im_detect2
from fast_rcnn.nms_wrapper import nms
from utils.timer import Timer
from utils.camera_to_marker import aruco_camPose
from utils.handy_SUPPORTABLE_binary import write_pddl

import numpy as np
import os, cv2
import argparse
import caffe
import time
import subprocess

### ROS STUFF
import rospy

# Message type for publishing can be reused
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Pose, Point, PoseStamped
from sensor_msgs.msg import Image, PointField, PointCloud2
import sensor_msgs.point_cloud2 as pc2
from handy_experiment.msg import action_msg
from std_msgs import msg
import cv_bridge
import matplotlib.pyplot as plt
#from ros_image_io import ImageIO



# start ros node and imageio
rospy.init_node('AffordanceNet_Node')
#pub_obj_pose_3D = rospy.Publisher("vs_obj_pose_3D", PoseStamped) # pose of object in camera frame
pub_point_cloud = rospy.Publisher('transformed_scene', PointCloud2)
pub_action_msg = rospy.Publisher('action_plan', action_msg)
#KINECT_FX = 525
#KINECT_FY = 525
#KINECT_CX = 319.5
#KINECT_CY = 239.5

KINECT_FX = 494.042
KINECT_FY = 490.682
KINECT_CX = 330.273
KINECT_CY = 247.443

CONF_THRESHOLD = 0.9
good_range = 0.005
    
# get current dir
cwd = os.getcwd()
root_path = os.path.abspath(os.path.join(cwd, os.pardir))  # get parent path
print 'AffordanceNet root folder: ', root_path
img_folder = cwd + '/img'

OBJ_CLASSES = ('__background__', 'bowl', 'cup', 'hammer', 'knife', 'ladle', 'mallet', 'mug', 'pot', 'saw', 'scissors','scoop','shears','shovel','spoon','tenderizer','trowel','turner')
OBJ_INDS = {'__background__' : 0, 'bowl' : 1, 'cup' : 2, 'hammer' : 3, 'knife' : 4,
            'ladle' : 5, 'mallet' : 6, 'mug' : 7, 'pot' : 8, 'saw' : 9, 'scissors' : 10, 'scoop' : 11, 'shears' : 12, 'shovel' : 13, 'spoon' : 14, 'tenderizer' : 15, 'trowel' : 16, 'turner' : 17}

OBJ_INDS_binary = {'__background__' : 0, 'target' : 1, 'tool' : 2 }
ACTION_INDS = {'pickup' : 0, 'dropoff' : 1}

# Mask
background = [200, 222, 250]  
c1 = [0,0,205] #grasp red  
c2 = [34,139,34] #cut green
c3 = [0,255,255] #scoop bluegreen 
c4 = [165,42,42] #contain dark blue   
c5 = [128,64,128] #pound purple 
c6 = [51,153,255] #support orange
c7 = [184,134,11] #wrap-grasp light blue
c8 = [0,153,153]
c9 = [0,134,141]
c10 = [184,0,141] 
c11 = [184,134,0] 
c12 = [184,134,223]
label_colours = np.array([background, c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12])

# Object
col0 = [0, 0, 0]
col1 = [0, 255, 255]
col2 = [255, 0, 255]
col3 = [0, 125, 255]
col4 = [55, 125, 0]
col5 = [255, 50, 75]
col6 = [100, 100, 50]
col7 = [25, 234, 54]
col8 = [156, 65, 15]
col9 = [215, 25, 155]
col10 = [25, 25, 155]
col11 = [100, 100, 50]#
col12 = [25, 234, 54]#
col13 = [156, 65, 15]#
col14 = [215, 25, 155]#
col15 = [25, 25, 155]#
col16 = [100, 100, 50]#
col17 = [184,134,11]

col_map = [col0, col1, col2, col3, col4, col5, col6, col7, col8, col9, col10, col11, col12, col13, col14, col15, col16, col17]



def reset_mask_ids(mask, before_uni_ids):
    # reset ID mask values from [0, 1, 4] to [0, 1, 2] to resize later 
    counter = 0
    for id in before_uni_ids:
        mask[mask == id] = counter
        counter += 1
        
    return mask
    

    
def convert_mask_to_original_ids_manual(mask, original_uni_ids):
    #TODO: speed up!!!
    temp_mask = np.copy(mask) # create temp mask to do np.around()
    temp_mask = np.around(temp_mask, decimals=0)  # round 1.6 -> 2., 1.1 -> 1.
    current_uni_ids = np.unique(temp_mask)
     
    out_mask = np.full(mask.shape, 0, 'float32')
     
    mh, mw = mask.shape
    for i in range(mh-1):
        for j in range(mw-1):
            for k in range(1, len(current_uni_ids)):
                if mask[i][j] > (current_uni_ids[k] - good_range) and mask[i][j] < (current_uni_ids[k] + good_range):  
                    out_mask[i][j] = original_uni_ids[k] 
                    #mask[i][j] = current_uni_ids[k]
           
#     const = 0.005
#     out_mask = original_uni_ids[(np.abs(mask - original_uni_ids[:,None,None]) < const).argmax(0)]
              
    #return mask
    return out_mask
        



def draw_arrow(image, p, q, color, arrow_magnitude, thickness, line_type, shift):
    # draw arrow tail
    cv2.line(image, p, q, color, thickness, line_type, shift)
    # calc angle of the arrow
    angle = np.arctan2(p[1]-q[1], p[0]-q[0])
    # starting point of first line of arrow head
    p = (int(q[0] + arrow_magnitude * np.cos(angle + np.pi/4)),
    int(q[1] + arrow_magnitude * np.sin(angle + np.pi/4)))
    # draw first half of arrow head
    cv2.line(image, p, q, color, thickness, line_type, shift)
    # starting point of second line of arrow head
    p = (int(q[0] + arrow_magnitude * np.cos(angle - np.pi/4)),
    int(q[1] + arrow_magnitude * np.sin(angle - np.pi/4)))
    # draw second half of arrow head
    cv2.line(image, p, q, color, thickness, line_type, shift)
    
def draw_reg_text(img, obj_info):
    #print 'tbd'
    
    obj_id = obj_info[0]
    cfd = obj_info[1]
    xmin = obj_info[2]
    ymin = obj_info[3]
    xmax = obj_info[4]
    ymax = obj_info[5]

    draw_arrow(img, (xmin, ymin), (xmax, ymin), col_map[obj_id], 0, 5, 8, 0)
    draw_arrow(img, (xmax, ymin), (xmax, ymax), col_map[obj_id], 0, 5, 8, 0)
    draw_arrow(img, (xmax, ymax), (xmin, ymax), col_map[obj_id], 0, 5, 8, 0)
    draw_arrow(img, (xmin, ymax), (xmin, ymin), col_map[obj_id], 0, 5, 8, 0)
    
    # put text
    txt_obj = OBJ_CLASSES[obj_id] + ' ' + str(cfd)
    cv2.putText(img, txt_obj, (xmin, ymin-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1) # draw with red
    #cv2.putText(img, txt_obj, (xmin, ymin), cv2.FONT_HERSHEY_SIMPLEX, 1, col_map[obj_id], 2)
    
#     # draw center
#     center_x = (xmax - xmin)/2 + xmin
#     center_y = (ymax - ymin)/2 + ymin
#     cv2.circle(img,(center_x, center_y), 3, (0, 255, 0), -1)
    
    return img



def visualize_mask_asus(im, rois_final, rois_class_score, rois_class_ind, masks, thresh):

    list_bboxes = []
    list_masks = []

    if rois_final.shape[0] == 0:
        print 'No object detection!'
        return list_bboxes, list_masks
    print(rois_class_score[:, -1])
    inds = np.where(rois_class_score[:, -1] >= thresh)[0]
    if len(inds) == 0:
        print 'No detected box with probality > thresh = ', thresh, '-- Choossing highest confidence bounding box.'
        inds = [np.argmax(rois_class_score)]  
        max_conf = np.max(rois_class_score)
        if max_conf < 0.001: 
            return list_bboxes, list_masks
            
    rois_final = rois_final[inds, :]
    rois_class_score = rois_class_score[inds,:]
    rois_class_ind = rois_class_ind[inds,:]
    
    # get mask
    masks = masks[inds, :, :, :]
    
    im_width = im.shape[1]
    im_height = im.shape[0]
    
    # transpose
    im = im[:, :, (2, 1, 0)]

    num_boxes = rois_final.shape[0]
    
    for i in xrange(0, num_boxes):
        
        curr_mask = np.full((im_height, im_width), 0.0, 'float') # convert to int later
            
        class_id = int(rois_class_ind[i,0])
    
        bbox = rois_final[i, 1:5]
        score = rois_class_score[i,0]
        
        if cfg.TEST.MASK_REG:

            x1 = int(round(bbox[0]))
            y1 = int(round(bbox[1]))
            x2 = int(round(bbox[2]))
            y2 = int(round(bbox[3]))

            x1 = np.min((im_width - 1, np.max((0, x1))))
            y1 = np.min((im_height - 1, np.max((0, y1))))
            x2 = np.min((im_width - 1, np.max((0, x2))))
            y2 = np.min((im_height - 1, np.max((0, y2))))
            
            cur_box = [class_id, score, x1, y1, x2, y2]
            list_bboxes.append(cur_box)
            
            h = y2 - y1
            w = x2 - x1
                        
            mask = masks[i, :, :, :]
            mask = np.argmax(mask, axis=0)
            
            original_uni_ids = np.unique(mask)
            
            # sort before_uni_ids and reset [0, 1, 7] to [0, 1, 2]
            original_uni_ids.sort()
            mask = reset_mask_ids(mask, original_uni_ids)
            
            mask = cv2.resize(mask.astype('float'), (int(w), int(h)), interpolation=cv2.INTER_LINEAR)
            #mask = convert_mask_to_original_ids(mask, original_uni_ids)
            mask = convert_mask_to_original_ids_manual(mask, original_uni_ids)
            
            # for mult masks
            curr_mask[y1:y2, x1:x2] = mask 
            
            # visualize each mask
            curr_mask = curr_mask.astype('uint8')
            list_masks.append(curr_mask)
            color_curr_mask = label_colours.take(curr_mask, axis=0).astype('uint8')
            cv2.imshow('Mask' + str(i), color_curr_mask)
            cv2.waitKey()
            #cv2.imwrite('mask'+str(i)+'.jpg', color_curr_mask)
            

    img_org = im.copy()
    for ab in list_bboxes:
        print 'box: ', ab
        img_out = draw_reg_text(img_org, ab)
    
    cv2.imshow('Obj Detection', img_out)
    #cv2.imwrite('obj_detction.jpg', img_out)
    #cv2.waitKey(0)
    
    return list_bboxes, list_masks


def get_list_centroid(current_mask, obj_id):
    list_uni_ids = list(np.unique(current_mask))
    list_uni_ids.remove(0) ## remove background id
    print list_uni_ids
    print obj_id
    
    list_centroid = []  ## each row is: obj_id, mask_id, xmean, ymean
    list_allIndex = [] 
    for val in list_uni_ids:
        inds = np.where(current_mask == val) 
        x_index = inds[1]
        y_index = inds[0]
        
        xmean = int(np.mean(x_index))
        ymean = int(np.mean(y_index))
        
        cur_centroid = [obj_id, val, xmean, ymean]
        cur_allIndex = [obj_id, val, x_index, y_index]
        list_centroid.append(cur_centroid)
        list_allIndex.append(cur_allIndex)
        
    return list_centroid, list_allIndex   


# This extended function binarize found objectness into (1) target (2) tool
# For simplicity, target is temporarily defined as objectness with only "GRASPABLE" affordance

def get_list_centroid_and_binary(current_mask, obj_id):
    list_uni_ids = list(np.unique(current_mask))
    list_uni_ids.remove(0) ## remove background id

    IS_TARGET = False
    if len(list_uni_ids) == 1 and list_uni_ids[0] == 1: # only "GRASPABLE"
        IS_TARGET = True
    
    list_centroid = []  ## each row is: obj_id, mask_id, xmean, ymean
    list_allIndex = [] 
    for val in list_uni_ids:
        inds = np.where(current_mask == val) 
        x_index = inds[1]
        y_index = inds[0]
        
        xmean = int(np.mean(x_index))
        ymean = int(np.mean(y_index))
        

        # add condition to filter out noise (total mask region less than threshold)
        print("filtering out mask region less than threshold")
        print("x_index len")
        print len(x_index)
        if len(x_index) < 1000:
            continue

        #cur_centroid = [obj_id, val, xmean, ymean]
        #cur_allIndex = [obj_id, val, x_index, y_index]
        #remap class label: 1 to target, 2 to tool
        if IS_TARGET:
            cur_centroid = [1, val, xmean, ymean]
            cur_allIndex = [1, val, x_index, y_index] 
        else:    
            cur_centroid = [2, val, xmean, ymean]
            cur_allIndex = [2, val, x_index, y_index] 

        list_centroid.append(cur_centroid)
        list_allIndex.append(cur_allIndex)
        
    return list_centroid, list_allIndex  


def convert_bbox_to_centroid(list_boxes, list_masks):
    assert len(list_boxes) == len(list_masks), 'ERROR: len(list_boxes) and len(list_masks) must be equal'
    list_final = []
    list_final_index = []
    for i in range(len(list_boxes)):
        obj_id = list_boxes[i][0] 
        list_centroids, list_allIndex = get_list_centroid_and_binary(list_masks[i], obj_id)  # return [[obj_id, mask_id, xmean, ymean]]
        if len(list_centroids) > 0:
            for l in list_centroids:
                list_final.append(l)
        if len(list_allIndex) > 0:
            for l in list_allIndex:
                list_final_index.append(l)
                
    return list_final, list_final_index


def select_object_and_aff(list_obj_centroids, obj_id, aff_id):
    # select the first object with object id and aff id
    selected_obj_aff = []
    for l in list_obj_centroids:
        if len(l) > 0:
            if l[0] == obj_id and l[1] == aff_id:
                selected_obj_aff.append(l)
                break
    
    selected_obj_aff = selected_obj_aff[0]
    return selected_obj_aff  

    
def project_to_3D(width_x, height_y, depth):
    X = (width_x - KINECT_CX) * depth / KINECT_FX
    Y = (height_y - KINECT_CY) * depth / KINECT_FY
    Z = depth
    p3D = [X, Y, Z]
    
    return p3D

def run_affordance_net_asus(net, im):
    tmp_g = im[:,:,1]
    im[:,:,1] = im[:,:,2] 
    im[:,:,2] = tmp_g  
    img = im.astype('uint8')
    # Detect all object classes and regress object bounds
    timer = Timer()
    timer.tic()
    if cfg.TEST.MASK_REG:
        rois_final, rois_class_score, rois_class_ind, masks, scores, boxes = im_detect2(net, im)
        # for some reason the kl model isnt working on landan's pc; we collect data from fu-jen's pc and transmit to landan 
        if args.sim and os.path.exists('/home/landan/data_shared/affordance/landan/support/im_detect2.npz'):
            container = np.load('/home/landan/data_shared/affordance/landan/support/im_detect2.npz')
            rois_final, rois_class_score, rois_class_ind, masks, scores, boxes = container['arr_0'], container['arr_1'], container['arr_2'], container['arr_3'], container['arr_4'], container['arr_5']
    else:
        1
    timer.toc()
    print ('Detection took {:.3f}s for '
           '{:d} object proposals').format(timer.total_time, rois_final.shape[0])
    
    # Visualize detections for each class
    return visualize_mask_asus(im, rois_final, rois_class_score, rois_class_ind, masks, thresh=CONF_THRESHOLD)


def parse_args():
    """Parse input arguments."""
    parser = argparse.ArgumentParser(description='AffordanceNet demo')
    parser.add_argument('--gpu', dest='gpu_id', help='GPU device id to use [0]',
                        default=0, type=int)
    parser.add_argument('--cpu', dest='cpu_mode',
                        help='Use CPU mode (overrides --gpu)',
                        action='store_true')
    parser.add_argument('--sim', help='Use simulated data',
                        action='store_true')

    args = parser.parse_args()

    return args

    

if __name__ == '__main__':
    cfg.TEST.HAS_RPN = True  # Use RPN for proposals

    args = parse_args()    

    prototxt = root_path + '/models/pascal_voc/VGG16/faster_rcnn_end2end/test_2nd.prototxt'
    caffemodel = root_path + '/pretrained/vgg16_faster_rcnn_iter_151000.caffemodel' 
    
    if not os.path.isfile(caffemodel):
        raise IOError(('{:s} not found.\n').format(caffemodel))

    if args.cpu_mode:
        caffe.set_mode_cpu()
    else:
        caffe.set_mode_gpu()
        caffe.set_device(args.gpu_id)
        cfg.GPU_ID = args.gpu_id
    
    # load network
    net = caffe.Net(prototxt, caffemodel, caffe.TEST)
    print '\n\nLoaded network {:s}'.format(caffemodel)

    # Load Kinect data
    print("Waiting for Kinect data...")
    if args.sim and os.path.exists('/home/landan/data_shared/affordance/landan/support/RGB.npy') and os.path.exists('/home/landan/data_shared/affordance/landan/support/depth.npy'):
        arr_rgb = np.load('/home/landan/data_shared/affordance/landan/support/RGB.npy')
        arr_depth = np.load('/home/landan/data_shared/affordance/landan/support/depth.npy')
        arr_rgb_show = np.concatenate((arr_rgb[:, :, 2:], arr_rgb[:, :, 1:2], arr_rgb[:, :, 0:1]), axis=2)
        import scipy.misc
        scipy.misc.imsave('screwdriver2turner.png', arr_rgb_show)
        plt.imshow(arr_rgb_show)
        plt.show()                 
    else:
        # Get image data from kinect
        rgb =  rospy.wait_for_message("/camera/rgb/image_color", Image)
        depth = rospy.wait_for_message("/camera/depth_registered/image_raw", Image)

        # Convert ROS image to OpenCV
        bridge = cv_bridge.CvBridge()
        rgb = bridge.imgmsg_to_cv2(rgb, desired_encoding="passthrough")
        depth = bridge.imgmsg_to_cv2(depth, desired_encoding="passthrough")

        # Convert OpenCV to numpy arrays
        arr_rgb = np.asarray(rgb[:, :, :])
        arr_depth = np.asarray(depth[:, :])
        
        # Change channels from BGR to RGB
        #arr_rgb = np.concatenate((arr_rgb[:, :, 2:], arr_rgb[:, :, 1:2], arr_rgb[:, :, 0:1]), axis=2)
        arr_rgb = np.concatenate((arr_rgb[:, :, 0:1], arr_rgb[:, :, 1:2], arr_rgb[:, :, 2:]), axis=2)

        plt.imshow(arr_rgb)
        plt.show()

        # Save data for easy use in the future
        if args.sim:
            np.save('rgb.npy', arr_rgb)
            np.save('depth.npy', arr_depth)
            import scipy.io as sio
            sio.savemat('rgb.mat', {'rgb':arr_rgb})
            sio.savemat('depth.mat', {'depth':arr_depth})
    

    # Get camera to aruco marker transformation
    marker_to_camera = aruco_camPose(arr_rgb)
    camera_to_marker = np.linalg.inv(marker_to_camera)
    
    if (arr_rgb.shape[0] > 100 and arr_rgb.shape[1] > 100):
        print '-------------------n-------------------------------------'
        list_boxes, list_masks = run_affordance_net_asus(net, arr_rgb)
        print 'len list boxes: ', len(list_boxes)
        list_obj_centroids, list_obj_centroids_index = convert_bbox_to_centroid(list_boxes, list_masks)
        print list_obj_centroids

        # Writes the problem .pddl file and is located at lib/utils/handy.py
        write_pddl('../pddl/', list_obj_centroids)
        
        # Generate the action plan using the fast-downward python script (alternative?)
        subprocess.call('~/fast-downward/fast-downward.py ../pddl/domain_SUPPORTABLE.pddl ../pddl/auto_problem_SUPPORTABLE_binary.pddl --search "astar(blind())"', shell=True)
        
        # Parse the plan generated by fast downward into a list of actions and objects
        plan = []
        with open('./sas_plan') as f:
            for i, line in enumerate(f.readlines()[:-1]):
                action = []
                # List of words in the current line of the sas_plan
                elements = line.split(' ')

                # Extract the action and convert it into an integer using the hashmap ACTION_INDS
                action_ind = ACTION_INDS[elements[0][1:]]
                action.append(action_ind)

                # Iterate through objects for the action
                for element in elements:
                    # Remove last parantheses (there is probably an easier way)
                    obj = element.split(')')[0]

                    # Map the object to an integer if it is in the list of possible objects
                    if obj in OBJ_INDS_binary:
                        action.append(OBJ_INDS_binary[obj])
                        
                plan.append(action)
    print("plan: ")
    print(plan)

    # Next few lines converts pixel coordinates to marker frame world coordinates for Rviz visualization
    width, height = arr_rgb.shape[:2]
    rows = np.arange(0, height)
    cols = np.arange(0, width)
    x, y = np.meshgrid(rows, cols)

    # Pixel coordinates with depth
    coords = np.concatenate([x.reshape(-1, 1), y.reshape(-1, 1), arr_depth.reshape(-1, 1)], axis=1).T.astype(float) # Nx3
    
    # Convert the pixel coordinates to 3D coordinates
    coords_3D = np.concatenate(project_to_3D(coords[np.newaxis, 0], coords[np.newaxis, 1], coords[np.newaxis, 2]), axis=0) # 3xN

    # Make homogeneous coordinates (concatenate row of 1s)
    coords_hom = np.concatenate([coords_3D/1000, np.ones((1, width*height))], axis=0) # 4xN

    # Convert coordinates from camera from into the marker frame
    coords_cam = np.dot(camera_to_marker, coords_hom) # 4xN

    # Replace 1s with rgb values
    arr_rgb = arr_rgb.astype(int)

    # following visualization of the point cloud, for efficiency, downsampling 100x
    #from matplotlib import pyplot
    #from mpl_toolkits.mplot3d import Axes3D

    #fig = pyplot.figure()
    #ax = Axes3D(fig)

    #ax.scatter(coords_cam[0][::100], coords_cam[1][::100], coords_cam[2][::100])
    #pyplot.show()

    # Add color to point cloud for Rviz (does not work!!)
    red = np.left_shift(arr_rgb[:, :, 0].reshape(-1), 16)
    green = np.left_shift(arr_rgb[:, :, 1].reshape(-1), 8)
    blue = arr_rgb[:, :, 2].reshape(-1)
    coords_cam[-1] = red + green + blue

    # Create point cloud 2 message
    fields = [PointField('x', 0, PointField.FLOAT32, 1),
              PointField('y', 4, PointField.FLOAT32, 1),
              PointField('z', 8, PointField.FLOAT32, 1),
              PointField('rgb', 16, PointField.FLOAT32, 1)]
    h = msg.Header()
    h.stamp = rospy.Time.now()
    h.frame_id = '/affordance_net'
    pc2_msg = pc2.create_cloud(h, fields, coords_cam.T)

    # Create an action message and populate its fields
    action_list = action_msg()
    action_list.header.frame_id = "camera_depth_optical_frame"
    for action in plan:
        action_list.action.append(action[0])
        
        # Iterate through objects
        for arg, obj in enumerate(action[1:]):
            width, height = [], []
            
            # If the action is pickup, select desired object centroid based on grasp (9)
            if action[0] == 0:
                #_, _, width, height = select_object_and_aff(list_obj_centroids, obj, 9)
                _, _, width, height = select_object_and_aff(list_obj_centroids_index, obj, 1)

            # If the action is dropoff, select desired object centroid based on contains (1)
            elif action[0] == 1:
                # check if it is the 2 argument (first is irrelevant, review .pddl files for info)
                if arg == 1:
                    #_, _, width, height = select_object_and_aff(list_obj_centroids, obj, 1)
                    _, _, width, height = select_object_and_aff(list_obj_centroids_index, obj, 6)

            # If the object with the correct affordance was found, add the pose to the action message
            if len(width) != 0 and len(height) != 0:
                print(width, height)
                depth = arr_depth[height, width].astype(float) / 1000
                
                # trim depth==0
                zeros_index = np.where(depth == 0)[0]
                width, height, depth = np.delete(width, zeros_index, None), np.delete(height, zeros_index, None), np.delete(depth, zeros_index, None)
                width_mean, height_mean, depth_mean = np.mean(width), np.mean(height), np.mean(depth)

                # TODO: check for null depth (?)
                # Convert camera frame coordinates to marker frame
                coords_cam = project_to_3D(width_mean, height_mean, depth_mean)
                coords_3D = np.dot(camera_to_marker, np.append(coords_cam, 1))
                print(coords_3D)
                # Add the pose attribute to the action message (+0.1, +0.28, -0.12 are used to transform relative to handy)
                obj_pose_3D = Pose()
                obj_pose_3D.position.x = round(coords_3D[0], 2) + 0.20 - 0.0672
                obj_pose_3D.position.y = round(coords_3D[1], 2) + 0.30
                obj_pose_3D.position.z = round(coords_3D[2], 2) - 0.13 
                obj_pose_3D.orientation.x = 0
                obj_pose_3D.orientation.y = 0
                obj_pose_3D.orientation.z = 0
                obj_pose_3D.orientation.w = 1

                action_list.pose.append(obj_pose_3D)
            
    # Print out the published message
    print(action_list)
    print("action_list printed")

    # Continously publish the point cloud for Rviz and an action message for pickplace_kinect.cpp
    try:
      while(1):
        pub_point_cloud.publish(pc2_msg)
        pub_action_msg.publish(action_list)
        time.sleep(10)

    except KeyboardInterrupt:
        print('interrupted!')
        
