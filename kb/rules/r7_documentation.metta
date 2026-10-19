(= (check-r7 $c)
   (if (has-fact (IcdCode $c $_))
       (Result R7 pass (stv 1.0 0.9) (detail (reason complete)))
       (Result R7 warn (stv 0.5 0.7) (detail (reason no_diagnosis)))))
