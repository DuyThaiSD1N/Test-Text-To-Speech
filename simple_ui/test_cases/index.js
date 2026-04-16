// ═══════════════════════════════════════════════════════════════════════
// TEST CASES INDEX - Import tất cả test cases
// ═══════════════════════════════════════════════════════════════════════

import { testCase01 } from './test_case_01.js';
import { testCase02 } from './test_case_02.js';
import { testCase03 } from './test_case_03.js';
import { testCase04 } from './test_case_04.js';
import { testCase05 } from './test_case_05.js';
import { testCase06 } from './test_case_06.js';
import { testCase07 } from './test_case_07.js';
import { testCase08 } from './test_case_08.js';
import { testCase09 } from './test_case_09.js';
import { testCase10 } from './test_case_10.js';
import { testCase11 } from './test_case_11.js';
import { testCase12 } from './test_case_12.js';
import { testCase13 } from './test_case_13.js';
import { testCase14 } from './test_case_14.js';
import { testCase15 } from './test_case_15.js';
import { testCase16 } from './test_case_16.js';
import { testCase17 } from './test_case_17.js';
import { testCase18 } from './test_case_18.js';
import { testCase19 } from './test_case_19.js';
import { testCase20 } from './test_case_20.js';
import { testCase21 } from './test_case_21.js';
import { testCase22 } from './test_case_22.js';

// Export tất cả test cases
export const allTestCases = [
    testCase01,
    testCase02,
    testCase03,
    testCase04,
    testCase05,
    testCase06,
    testCase07,
    testCase08,
    testCase09,
    testCase10,
    testCase11,
    testCase12,
    testCase13,
    testCase14,
    testCase15,
    testCase16,
    testCase17,
    testCase18,
    testCase19,
    testCase20,
    testCase21,
    testCase22
];

// Export theo category (optional - để dễ filter)
export const testCasesByCategory = {
    basic: [testCase01, testCase02, testCase03], // Mua cơ bản
    promotion: [testCase04, testCase11, testCase12, testCase13, testCase14], // Liên quan ưu đãi
    information: [testCase05, testCase06, testCase07, testCase08], // Hỏi thông tin
    expiry: [testCase09, testCase21], // Liên quan hết hạn
    existing: [testCase10, testCase11], // Đã có BH
    rejection: [testCase13, testCase14, testCase15], // Từ chối rồi đổi ý
    advanced: [testCase16, testCase17, testCase18, testCase19, testCase20, testCase22] // Nâng cao
};
