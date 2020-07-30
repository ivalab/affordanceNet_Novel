# get object centroids, convert index to actual object name, check if object has desired affordance
#  i.e. graspable and contains

# TODO: deal with identifical objects of the same type
import os

OBJ_CLASSES = ('__background__', 'bowl', 'cup', 'hammer', 'knife', 'ladle', 'mallet', 'mug', 'pot', 'saw', 'scissors','scoop','shears','shovel','spoon','tenderizer','trowel','turner')
AFF_CLASSES = ('', 'GRASPABLE', '', '', 'CONTAINABLE', '', 'SUPPORTABLE', '', '', '')


def write_pddl(path, list_obj_centroids):
    """
    Generates the problem .pddl based on the scene captured by the Kinect

    Parameters:
    -----------
    path: str
         The location that the auto_problem.pddl file will be saved

    list_obj_centroids: list of tuples
         A list of objects and affordances detected with AffordanceNet
    """
    
    define =  '(define (problem handy_vision)\n'
    domain =  '    (:domain handy)\n'
    objects = '    (:objects arm '
    init =    '    (:init (free arm) '
    goal =    '    (:goal (and (supports turner shears))))'
    
    # add objects to .pddl
    for obj in list_obj_centroids:
        # Check if it is background
        if obj[0] != 0:
            # Get the object and affordance classes
            obj_class = OBJ_CLASSES[obj[0]]
            aff_class = AFF_CLASSES[obj[1]]

            # Do not add object if already added (needs to be fixed if objects of the same class will be used)
            if obj_class not in objects:
                objects += (obj_class + ' ')
            # If an affordance is detected
            if  aff_class:
                init += ('(' + aff_class + ' ' + obj_class + ') ')

    # end strings
    objects += ')\n'
    init += ')\n'
    with open(os.path.join(path, 'auto_problem_SUPPORTABLE.pddl'), 'w') as f:
        f.write(define + domain + objects + init + goal)
        
        
