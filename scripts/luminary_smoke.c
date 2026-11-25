#include <stdio.h>

#include "yaAGC.h"
#include "agc_engine.h"

enum { SMOKE_CYCLES = 4096 };
static agc_t state;

int main(int argc, char **argv)
{
    if (argc != 2) {
        fprintf(stderr, "usage: luminary_smoke <verified rope>\n");
        return 2;
    }

    int result = agc_engine_init(&state, argv[1], NULL, 0);
    if (result != 0) {
        fprintf(stderr, "yaAGC could not initialize the rope (code %d)\n", result);
        return 1;
    }

    unsigned initial_pc = state.Erasable[0][RegZ];
    for (unsigned cycle = 0; cycle < SMOKE_CYCLES; ++cycle) {
        if (agc_engine(&state) != 0) {
            fprintf(stderr, "yaAGC failed at cycle %u\n", cycle);
            return 1;
        }
    }

    unsigned final_pc = state.Erasable[0][RegZ];
    if (state.CycleCounter != SMOKE_CYCLES || initial_pc != 04000 || final_pc != 06521) {
        fprintf(stderr, "unexpected boot state after %llu cycles: %04o -> %04o\n",
                (unsigned long long)state.CycleCounter, initial_pc, final_pc);
        return 1;
    }

    printf("{\"cycles\": %llu, \"initial_pc\": \"%04o\", \"final_pc\": \"%04o\"}\n",
           (unsigned long long)state.CycleCounter, initial_pc, final_pc);
    return 0;
}
