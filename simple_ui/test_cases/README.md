# Test Cases - Cấu trúc mới

## 📁 Cấu trúc

```
simple_ui/test_cases/
├── index.js              # Import và export tất cả test cases
├── test_case_01.js       # TC01: Bảo hiểm xe máy
├── test_case_02.js       # TC02: Bảo hiểm ô tô
├── test_case_03.js       # TC03: Mua ngay từ đầu
├── test_case_04.js       # TC04: Mua sau khi nghe ưu đãi
├── test_case_05.js       # TC05: Mua sau khi hiểu quyền lợi
├── test_case_06.js       # TC06: Hỏi giá nhiều lần
├── test_case_07.js       # TC07: Hỏi nguồn thông tin
├── test_case_08.js       # TC08: Hỏi nhiều thông tin
├── test_case_09.js       # TC09: Chưa rõ thời hạn BH
├── test_case_10.js       # TC10: Đã mua BH nhưng muốn biết thêm
├── test_case_11.js       # TC11: Đã mua BH sắp hết hạn
├── test_case_12.js       # TC12: Đổi nhà cung cấp mới
├── test_case_13.js       # TC13: Từ chối rồi quay đầu mua
├── test_case_14.js       # TC14: Giá đắt nhưng có ưu đãi
├── test_case_15.js       # TC15: Không quan tâm rồi đổi ý
├── test_case_16.js       # TC16: Còn hạn dài - Gửi thông tin
├── test_case_17.js       # TC17: Hỏi cách dùng BH khi tai nạn
├── test_case_18.js       # TC18: Hỏi về uy tín BH
├── test_case_19.js       # TC19: Hỏi cách đóng tiền
├── test_case_20.js       # TC20: Mua để tên người khác
├── test_case_21.js       # TC21: Nhầm lẫn còn hạn BH
└── test_case_22.js       # TC22: Hỏi lại toàn bộ trước khi mua
```

## 🎯 Danh sách Test Cases

### Nhóm 1: Mua cơ bản (TC01-03)
- **TC01**: Bảo hiểm xe máy - Hỏi giá và mua
- **TC02**: Bảo hiểm ô tô - Hỏi giá và mua
- **TC03**: Mua ngay từ đầu - Agent hỏi loại xe

### Nhóm 2: Liên quan ưu đãi (TC04, TC11-14)
- **TC04**: Mua sau khi nghe ưu đãi
- **TC11**: Đã mua BH sắp hết hạn + nghe ưu đãi
- **TC12**: Đổi nhà cung cấp mới có ưu đãi
- **TC13**: Từ chối nhưng nghe ưu đãi thì quay đầu
- **TC14**: Giá đắt, từ chối nhưng nghe ưu đãi thì đổi ý

### Nhóm 3: Hỏi thông tin (TC05-08)
- **TC05**: Mua sau khi hiểu quyền lợi và bảo hiểm là gì
- **TC06**: Hỏi giá nhiều lần rồi mua
- **TC07**: Hỏi nguồn thông tin rồi tin tưởng
- **TC08**: Hỏi nhiều thông tin chi tiết

### Nhóm 4: Liên quan hết hạn (TC09, TC21)
- **TC09**: Chưa rõ thời hạn, sau khi biết gần hết hạn thì mua
- **TC21**: Nhầm lẫn còn hạn, agent báo lại đúng

### Nhóm 5: Đã có BH (TC10-11)
- **TC10**: Đã mua BH nhưng vẫn muốn biết thông tin
- **TC11**: Đã mua BH sắp hết hạn + nghe ưu đãi

### Nhóm 6: Từ chối rồi đổi ý (TC13-15)
- **TC13**: Từ chối, agent báo ưu đãi thì quay đầu
- **TC14**: Giá đắt, từ chối nhưng nghe ưu đãi thì đổi ý
- **TC15**: Không quan tâm, nghe lợi ích thì đổi ý

### Nhóm 7: Nâng cao (TC16-22)
- **TC16**: Còn hạn dài, agent báo giá thì khách bảo gửi thông tin
- **TC17**: Hỏi lỡ có tai nạn thì BH dùng như thế nào
- **TC18**: Hỏi về tính uy tín, thực tế của BH
- **TC19**: Hỏi về cách đóng tiền (chuyển khoản/trực tiếp)
- **TC20**: Muốn mua nhưng để tên người khác
- **TC21**: Nhầm lẫn còn hạn, agent báo lại đúng
- **TC22**: Chuẩn bị mua thì hỏi lại toàn bộ thông tin

## 📝 Cấu trúc mỗi Test Case

```javascript
export const testCaseXX = {
    id: 'tcXX',
    title: 'TCXX: Tên test case',
    description: 'Mô tả ngắn gọn',
    steps: [
        'Bước 1',
        'Bước 2',
        // ...
    ],
    data: {
        title: 'anh/chị',
        name: 'Tên khách hàng',
        plate: 'Biển số xe',
        expire: 'YYYY-MM-DD'
    },
    userMessages: [
        'Message 1 từ user ảo',
        'Message 2 từ user ảo',
        // ...
    ],
    validations: [
        { type: 'greeting', keywords: ['xin chào', 'anh'] },
        { type: 'price', keywords: ['giá', 'phí'] },
        // ...
    ]
};
```

## 🔧 Cách thêm Test Case mới

1. Tạo file mới: `test_case_XX.js`
2. Copy template từ test case có sẵn
3. Sửa nội dung theo kịch bản
4. Import vào `index.js`:
   ```javascript
   import { testCaseXX } from './test_case_XX.js';
   ```
5. Thêm vào array `allTestCases`:
   ```javascript
   export const allTestCases = [
       // ... existing
       testCaseXX
   ];
   ```

## ✅ Lợi ích của cấu trúc mới

1. **Dễ quản lý**: Mỗi test case 1 file riêng
2. **Dễ tìm kiếm**: Tên file rõ ràng (test_case_01.js)
3. **Dễ mở rộng**: Thêm test case mới không ảnh hưởng code cũ
4. **Dễ review**: Xem từng test case độc lập
5. **Tránh conflict**: Nhiều người có thể làm song song

## 🚀 Sử dụng

Test cases được tự động load khi mở UI:
```
http://localhost:8000/
```

Click vào nút "🧪 Thử Test Cases" để xem danh sách và chạy test.
