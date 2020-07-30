(define (problem handy_vision)
    (:domain handy)
    (:objects cup bowl arm)

    (:init (GRASPABLE cup) (CONTAINABLE bowl)
           (free arm))

    (:goal (and (contains bowl cup)))

)
    