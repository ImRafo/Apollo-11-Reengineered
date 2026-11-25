#include <ctype.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>

#include "yaAGC.h"
#include "agc_engine.h"

enum { MAX_CYCLES = 128, REGISTER_MASK = 0177777, WORD_MASK = 077777 };
static const unsigned slots[] = { RegA, RegL, RegQ, 0100, 0101, 0102, 0103, RegCYR };
static agc_t initial;
static agc_t state;

static int read_octal(const char **cursor, unsigned limit, unsigned *value)
{
    while (isspace((unsigned char)**cursor)) {
        ++*cursor;
    }
    if (**cursor < '0' || **cursor > '7') {
        return 0;
    }

    char *end;
    errno = 0;
    unsigned long number = strtoul(*cursor, &end, 8);
    if (errno || number > limit || (*end && !isspace((unsigned char)*end))) {
        return 0;
    }
    *value = (unsigned)number;
    *cursor = end;
    return 1;
}

static int load_case(const char *line, unsigned entry)
{
    state = initial;
    for (unsigned i = 0; i < sizeof(slots) / sizeof(slots[0]); ++i) {
        unsigned address = slots[i];
        unsigned limit = (address == RegA || address == RegQ) ? REGISTER_MASK : WORD_MASK;
        unsigned value;
        if (!read_octal(&line, limit, &value)) {
            return 0;
        }
        state.Erasable[0][address] =
            address == RegL ? SignExtend((int16_t)value) : (int16_t)value;
    }
    while (isspace((unsigned char)*line)) {
        ++line;
    }
    state.Erasable[0][RegZ] = (int16_t)entry;
    state.AllowInterrupt = 0;
    return *line == '\0';
}

static int run_case(unsigned stop)
{
    while (state.CycleCounter < MAX_CYCLES) {
        if (agc_engine(&state) != 0) {
            return 0;
        }
        if ((unsigned)state.Erasable[0][RegZ] == stop && !state.PendFlag && !state.ExtraDelay) {
            printf("%llu", (unsigned long long)state.CycleCounter);
            for (unsigned i = 0; i < sizeof(slots) / sizeof(slots[0]); ++i) {
                printf(" %06o", (unsigned)state.Erasable[0][slots[i]] & REGISTER_MASK);
            }
            printf(" %06o %06o %06o %06o %u %u\n",
                   (unsigned)state.Erasable[0][RegEB] & REGISTER_MASK,
                   (unsigned)state.Erasable[0][RegFB] & REGISTER_MASK,
                   (unsigned)state.Erasable[0][RegBB] & REGISTER_MASK,
                   (unsigned)state.IndexValue & REGISTER_MASK,
                   state.ExtraCode, state.AllowInterrupt);
            return 1;
        }
    }
    return 0;
}

int main(int argc, char **argv)
{
    unsigned entry, stop;
    if (argc != 4) {
        fprintf(stderr, "usage: agc_probe <rope> <octal entry> <octal checkpoint>\n");
        return 2;
    }
    const char *start_arg = argv[2];
    const char *stop_arg = argv[3];
    if (!read_octal(&start_arg, 07777, &entry) || *start_arg ||
        !read_octal(&stop_arg, 07777, &stop) || *stop_arg ||
        entry < 04000 || stop < 04000 || entry == stop) {
        fprintf(stderr, "probe needs distinct fixed-fixed entry and checkpoint addresses\n");
        return 2;
    }
    if (agc_engine_init(&initial, argv[1], NULL, 0) != 0) {
        fprintf(stderr, "yaAGC could not initialize the probe rope\n");
        return 1;
    }

    char line[128];
    unsigned row = 0;
    while (fgets(line, sizeof(line), stdin)) {
        ++row;
        if (!load_case(line, entry)) {
            fprintf(stderr, "invalid input vector on row %u\n", row);
            return 2;
        }
        if (!run_case(stop)) {
            fprintf(stderr, "row %u failed to reach %04o from %04o within %u MCT\n",
                    row, stop, entry, MAX_CYCLES);
            return 1;
        }
    }
    return ferror(stdin) || ferror(stdout);
}
