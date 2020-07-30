(define (domain handy)
    (:predicates (GRASPABLE ?x)
                 (carry ?x ?y)
		 (free ?x)
                 (SUPPORTABLE ?x)
		 (supports ?x ?y))

    (:action pickup :parameters(?x ?y)
        :precondition (and (GRASPABLE ?x)
	                   (free ?y))
			   
        :effect       (and (carry ?y ?x)
	                   (not (free ?y))
	                   (not (GRASPABLE ?x))))

    (:action dropoff :parameters (?x ?y ?z)
        :precondition (and (carry ?y ?x)
	                   (SUPPORTABLE ?z))
			   
	:effect       (and (supports ?z ?x)
                           (GRASPABLE ?x)
	                   (free ?y)
			   (not (carry ?y ?x))))

)
	                   
