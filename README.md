# AffordanceNet_DA
This is the implementation of our RA-L work 'Toward Affordance Detection and Ranking on Novel Objects for Real-world Robotic Manipulation'. This paper presents a framework to detect and rank affordances of novel objects to assist with robotic manipulation tasks. The original arxiv paper can be found [here](https://ieeexplore.ieee.org/abstract/document/8770077).

<p align="center">
<img src="https://github.com/ivalab/affordanceNet_Novel/blob/master/fig/concept.png" alt="drawing" width="300"/>
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
    - trained model for DEMO on [dropbox](https://www.dropbox.com/s/34v4pps8ug6s7x1/vgg16_faster_rcnn_iter_151000.caffemodel?dl=0) 
    - put under `./pretrained/`

5. Demo
```
cd $AffordanceNet_Novel_ROOT/tools
python demo_img_kldivergence.py
```
you can adjust `RANK` to be 1 or 2 or 3 
	
### Training
1. We train AffordanceNet_Novel on UMD dataset
	- You will need synthetic data and real data in Pascal dataset format. 
	- For your convinience, we did it for you. Just download this file on [dropbox](https://www.dropbox.com/s/zfgn3jo8b2zid7a/VOCdevkit2012.tar.gz?dl=0) and extract it into your `$AffordanceNet_Novel_ROOT/data` folder; And download this [Annotations](https://www.dropbox.com/home/gt/IVAlab/Deep_Learning_Project/data/affordanceNovel/Annotations_objectness) containing xml with `objectness` instead of all objects to replace `$AffordanceNet_Novel_ROOT/data/VOCdevkit2012/VOC2012/Annotations`; And download this file on [dropbox](https://www.dropbox.com/s/zfgn3jo8b2zid7a/VOCdevkit2012.tar.gz?dl=0) and extract it into your `$AffordanceNet_Novel_ROOT/data/cache` folder; Make sure you use the category split on [dropbox](https://www.dropbox.com/sh/bahp8aci3ejpytx/AAAlLD1L31XVuOSPzffNJkHya?dl=0) and extract it into your `$AffordanceNet_Novel_ROOT/data/VOCdevkit2012/VOC2012/ImageSets/Main` folder
	- You will need the VGG-16 weights pretrained on imagenet. For your convinience, please find it [here](https://www.dropbox.com/s/i4kv0vgn078d1jb/VGG16.v2.caffemodel?dl=0)
	- Put the weight into `$AffordanceNet_Novel_ROOT/imagenet_models`
	- If you want novel instance split, please find it [here](https://www.dropbox.com/sh/ya5n61prbc8ftum/AABABu3mqQW438BldvVUYmwoa?dl=0)

2. Train AffordanceNet_Novel:
```
cd $AffordanceNet_ROOT
./experiments/scripts/faster_rcnn_end2end.sh 0 VGG16 pascal_voc
```

### License
MIT License

### Acknowledgment
This repo borrows tons of code from
- [affordanceNet](https://github.com/nqanh/affordance-net) by nqanh


### Contact
If you encounter any questions, please contact me at fujenchu[at]gatech[dot]edu


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



