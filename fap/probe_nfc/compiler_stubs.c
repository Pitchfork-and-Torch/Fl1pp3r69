/* ARM GCC parity builtin used by libnfc — not exported via firmware API. */
unsigned int __paritysi2(unsigned int x) {
    x ^= x >> 16;
    x ^= x >> 8;
    x ^= x >> 4;
    x &= 0xF;
    return (0x6996U >> x) & 1U;
}