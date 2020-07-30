import sys
import cv2
import cv2.aruco as aruco
import numpy as np
import tf

def aruco_camPose(image):
    #cap = cv2.VideoCapture(0)

    if image is not None:

        gray = image.astype(np.uint8)

        parameters = aruco.DetectorParameters_create()

        # get the ref marker M_CL here
        #aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_250)
        aruco_dict_CL = aruco.Dictionary_get(aruco.DICT_ARUCO_ORIGINAL)

        corners_CL, ids_CL, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict_CL, parameters=parameters)
        cameraMatrix = np.array([[526.37013657, 0.00000000, 313.68782938], [0.00000000, 526.37013657, 259.01834898], [0.00000000, 0.00000000, 1.00000000]])
        distCoeffs = np.array([-0.02067, 0.06351, -0.00285, 0.00083, 0.00000])

        markerLength_CL = 0.093
        M_CL = np.zeros((4, 4))
        if ids_CL is not None:
          rvec_CL, tvec_CL, _objPoints_CL = aruco.estimatePoseSingleMarkers(corners_CL[0], markerLength_CL, cameraMatrix, distCoeffs)
          dst_CL, jacobian_CL = cv2.Rodrigues(rvec_CL)

          M_CL[:3, :3] = dst_CL
          M_CL[:3, 3] = tvec_CL
          M_CL[3, :] = np.array([0, 0, 0, 1])

        print(M_CL)
        q = tf.transformations.quaternion_from_matrix(M_CL)
        return M_CL
