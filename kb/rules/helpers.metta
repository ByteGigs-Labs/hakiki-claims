;; Bindings leak out of unify, so give every wildcard in a rule its own variable name.
(= (has-fact $fact) (unify &self $fact True False))

(= (emergency $c)
   (match &self (ClaimService $c $s)
      (if (has-fact (Emergency $c)) True (has-fact (EmergencyService $s)))))
