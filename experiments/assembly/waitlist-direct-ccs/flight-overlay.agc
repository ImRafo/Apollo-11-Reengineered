                CCS     LONGTIME    # Test the erasable high word directly.
                TCF     LONGCYCL
                TCF     +3          # +0 enters the following low-word check.
                TCF     LONGPOOH
                TCF     +1          # -0 enters the same low-word check.
