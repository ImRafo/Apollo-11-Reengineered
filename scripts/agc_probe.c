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

static int16_t *erasable(unsigned address)
{
    return &state.Erasable[address / 0400][address % 0400];
}

static unsigned slot_address(unsigned index, unsigned x_address)
{
    return index == 3 ? x_address : slots[index];
}

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

static int read_argument(const char *argument, unsigned limit, unsigned *value)
{
    return read_octal(&argument, limit, value) && !*argument;
}

static int load_case(const char *line, unsigned entry, unsigned bank, unsigned x_address)
{
    state = initial;
    for (unsigned i = 0; i < sizeof(slots) / sizeof(slots[0]); ++i) {
        unsigned address = slot_address(i, x_address);
        unsigned limit = (address == RegA || address == RegQ) ? REGISTER_MASK : WORD_MASK;
        unsigned value;
        if (!read_octal(&line, limit, &value)) {
            return 0;
        }
        *erasable(address) = address == RegL ? SignExtend((int16_t)value) : (int16_t)value;
    }
    while (isspace((unsigned char)*line)) {
        ++line;
    }
    state.Erasable[0][RegZ] = (int16_t)entry;
    state.Erasable[0][RegFB] = (int16_t)(bank << 10);
    state.Erasable[0][RegBB] = state.Erasable[0][RegFB];
    state.AllowInterrupt = 0;
    return *line == '\0';
}

static int run_case(unsigned stop, unsigned x_address)
{
    while (state.CycleCounter < MAX_CYCLES) {
        if (agc_engine(&state) != 0) {
            return 0;
        }
        if ((unsigned)state.Erasable[0][RegZ] == stop && !state.PendFlag && !state.ExtraDelay) {
            printf("%llu", (unsigned long long)state.CycleCounter);
            for (unsigned i = 0; i < sizeof(slots) / sizeof(slots[0]); ++i) {
                printf(" %06o", (unsigned)*erasable(slot_address(i, x_address)) & REGISTER_MASK);
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
    unsigned bank = 0, x_address = 0100;
    if (argc != 4 && argc != 6) {
        fprintf(stderr, "usage: agc_probe <rope> <entry> <checkpoint> [<bank> <X address>] (octal)\n");
        return 2;
    }
    unsigned first_address = argc == 6 ? 02000 : 04000;
    unsigned last_address = argc == 6 ? 03777 : 07777;
    if (!read_argument(argv[2], last_address, &entry) ||
        !read_argument(argv[3], last_address, &stop) ||
        entry < first_address || stop < first_address || entry == stop) {
        fprintf(stderr, "probe needs distinct addresses in the selected fixed-memory window\n");
        return 2;
    }
    if (argc == 6 && (!read_argument(argv[4], 037, &bank) ||
                      !read_argument(argv[5], 01377, &x_address) || x_address < 0100 ||
                      (x_address >= 0101 && x_address <= 0103))) {
        fprintf(stderr, "probe bank or unswitched X address is out of range\n");
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
        if (!load_case(line, entry, bank, x_address)) {
            fprintf(stderr, "invalid input vector on row %u\n", row);
            return 2;
        }
        if (!run_case(stop, x_address)) {
            fprintf(stderr, "row %u failed to reach %04o from %04o within %u MCT\n",
                    row, stop, entry, MAX_CYCLES);
            return 1;
        }
    }
    return ferror(stdin) || ferror(stdout);
}
