## Page 1
# Standalone comment

BASE            SETLOC  4000
1/4             OCT     20000
LOOP            CA      1/4      # Inline comment
                EXTEND
                MP      1/4
                DLOAD
                        1/4
 +1             TC      LOOP
NEXT
$other.agc      # Include marker
                NOTANOP A
$
