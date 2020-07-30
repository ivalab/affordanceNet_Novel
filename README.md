# AffordanceNet_DA
This is the implementation of our RA-L work 'Toward Affordance Detection and Ranking on Novel Objects for Real-world Robotic Manipulation'. This paper presents a framework to detect and rank affordances of novel objects to assist with robotic manipulation tasks. The original arxiv paper can be found [here](https://ieeexplore.ieee.org/abstract/document/8770077).

<p align="center">
<img src="https://github.com/ivalab/affordanceNet_DA/blob/damask/fig/overlap_fewdigit.png" alt="drawing" width="300"/>
</p>

If you find it helpful for your research, please consider citing:

    @inproceedings{chu2019toward,
      title = {Learning Affordance Segmentation for Real-world Robotic Manipulation via Synthetic Images},
      author = {Chu, Fu-Jen and Xu, Ruinian and Seguin, Landan and Vela, Patricio A},
      journal = {IEEE Robotics and Automation Letters},
      year = {2019},
      volume={4},
      number={4},
      pages={4070--4077},    
      DOI = {10.1109/LRA.2019.2930364},
      ISSN = {4070-4077},
      month = {Oct}
    }

------------------------------------

### Requirements

1. Caffe:
	- Install Caffe: [Caffe installation instructions](http://caffe.berkeleyvision.org/installation.html).
	- Caffe must be built with support for Python layers.
	- You will need the modified caffe layer in this repository. Please make sure you clone from here.

2. Specifications:
	- CuDNN-5.1.10
	- CUDA-8.0


### Demo

1. Clone the AffordanceNet_DA repository into your `$AffordanceNet_Novel_ROOT` folder
```
git clone https://github.com/ivalab/affordanceNet_Novel.git
cd affordanceNet_Novel
```

2. Export pycaffe path
```
`export PYTHONPATH=$AffordanceNet_Novel_ROOT/caffe-affordance-net/python:$PYTHONPATH`
```

2. Build Cython modules
```
cd $AffordanceNet_Novel_ROOT/lib
make clean
make
cd ..
```

4. Download pretrained models
    - trained model for DEMO on [dropbox](https://www.dropbox.com/s/u28kllclmv8rb6f/vgg16_faster_rcnn_iter_70000.caffemodel?dl=0) 
    - put under `./pretrained/`

5. Demo
```
cd $AffordanceNet_Novel_ROOT/tools
python demo_img.py

	
### Training

1. We train AffordanceNet on [IIT-AFF dataset](https://sites.google.com/site/iitaffdataset/)
	- We need to format IIT-AFF dataset as in Pascal-VOC dataset for training.
	- For your convinience, we did it for you. Just download this file ([Google Drive](https://drive.google.com/file/d/0Bx3H_TbKFPCjV09MbkxGX0k1ZEU/view?usp=sharing), [One Drive](https://studenthcmusedu-my.sharepoint.com/:u:/g/personal/nqanh_mso_hcmus_edu_vn/EXQok71Y2kFAmhaabY2TQO8BFIO1AqqH5GcMOfPqgn_q2g?e=7rH3Kd)) and extract it into your `$AffordanceNet_ROOT` folder.
	- The extracted folder should contain three sub-folders: `$AffordanceNet_ROOT/data/cache`, `$AffordanceNet_ROOT/data/imagenet_models`, and `$AffordanceNet_ROOT/data/VOCdevkit2012` .

2. Train AffordanceNet:
	- `cd $AffordanceNet_ROOT`
	- `./experiments/scripts/faster_rcnn_end2end.sh [GPU_ID] [NET] [--set ...]`
	- e.g.: `./experiments/scripts/faster_rcnn_end2end.sh 0 VGG16 pascal_voc`
	- We use `pascal_voc` alias although we're training using the IIT-AFF dataset.



### Notes
1. AffordanceNet vs. Mask-RCNN: AffordanceNet can be considered as a general version of Mask-RCNN when we have multiple classes inside each instance.
2. The current network achitecture is slightly diffrent from the paper, but it achieves the same accuracy.
3. Train AffordanceNet on your data:
	- Format your images as in Pascal-VOC dataset (as in `$AffordanceNet_ROOT/data/VOCdevkit2012` folder).
	- Prepare the affordance masks (as in `$AffordanceNet_ROOT/data/cache` folder): For each object in the image, we need to create a mask and save as a .sm file. See `$AffordanceNet_ROOT/utils` for details.


### Citing AffordanceNet

If you find AffordanceNet useful in your research, please consider citing:

	@inproceedings{AffordanceNet18,
	  title={AffordanceNet: An End-to-End Deep Learning Approach for Object Affordance Detection},
	  author={Do, Thanh-Toan and Nguyen, Anh and Reid, Ian},
	  booktitle={International Conference on Robotics and Automation (ICRA)},
	  year={2018}
	}


If you use [IIT-AFF dataset](https://sites.google.com/site/iitaffdataset/), please consider citing:

	@inproceedings{Nguyen17,
	  title={Object-Based Affordances Detection with Convolutional Neural Networks and Dense Conditional Random Fields},
	  author={Nguyen, Anh and Kanoulas, Dimitrios and Caldwell, Darwin G and Tsagarakis, Nikos G},
	  booktitle = {IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS)},
	  year={2017},
	}


### License
MIT License

### Acknowledgement
This repo used a lot of source code from [Faster-RCNN](https://github.com/rbgirshick/py-faster-rcnn)


### Contact
If you have any questions or comments, please send us an email: `thanh-toan.do@adelaide.edu.au` and `anh.nguyen@iit.it`


### Modifications
1. [Annotations](https://www.dropbox.com/home/gt/IVAlab/Deep_Learning_Project/data/affordanceNovel/Annotations_objectness) contains xml with `objectness` instead of all objects, (and corresponding model descriptions for two classes)   
2. Modify proposal_target_layer.py
3. to modify affordance number: (1) no prototxt: "mask_score" (2) no config: __C.TRAIN.CLASS_NUM = 13 (3) no proposal_target_layer: label_colors (4) yes proposal_target_layer: label2dist

### Physical Grasping with PDDL

#### on Main PC
1. run objectness affordance saver
```
cd projects/affordanceSeg/affordance-net-da/tools
python demo_img_socket_noprocess_firstAff_kinect_LANDAN.py
```
if it takes long time to load kinect, run this first
```
cd projects/robotArm/aruco_tag/aruco_tag_saver
python camera_demo_arucoTag_kinect.py
```

2. move saved data to `/media/fujenchu/home3/data_shared/affordance/landan/AFFORDANCE` from `/media/fujenchu/home3/data_shared/affordance/landan/`

3. share folder
```
sudo sevice smbd restart
```

#### on LANDAN PC
1. run Handy
```
cd handy_ws
...
roslaunch handy_experiment pickplace_pddl.launch
```
2. run camera
```
roslaunch freenect_launch freenect.launch depth_registration:=true
```
3. run PDDL
```
cd affordance-net/scripts
python kinect_pddl_UMD_firstAffordance_objectness_nonprimary.py --sim
```
4. share folder
```
sudo mount -t cifs //143.215.144.24/data_shared /home/landan/data_shared -o username=fujenchu,password=fujenchu
```



