// Run with a native C++11 or later compiler. No serial port or hardware access.
#include <stdio.h>
#include "../gap_self_tests.h"
int main() {
    const gaplink::TestResult result = gaplink::self_test();
    printf("SELFTEST %s checks=%u failed=%u first=%s\n",
        result.failed ? "FAIL" : "PASS", result.checks, result.failed,
        result.first_failure ? result.first_failure : "none");
    return result.failed ? 1 : 0;
}
