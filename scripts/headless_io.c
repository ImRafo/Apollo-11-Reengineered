#include "yaAGC.h"
#include "agc_engine.h"

/* Headless runners neither record backtraces nor read interactive input. */
void BacktraceAdd(agc_t *cpu, int cause)
{
    (void)cpu;
    (void)cause;
}

void UnblockSocket(int descriptor)
{
    (void)descriptor;
}
