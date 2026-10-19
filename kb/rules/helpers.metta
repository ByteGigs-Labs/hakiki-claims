(= (has-fact $fact) (unify &self $fact True False))
(= (evaluable $c $then $else)
   (match &self (, (ClaimService $c $s) (ClaimFund $c $f))
      (if (has-fact (Service $s)) $then $else)))
