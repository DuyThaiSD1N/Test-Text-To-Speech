// TC22: Chuẩn bị mua thì hỏi lại toàn bộ thông tin
export const testCase22 = {
    id: 'tc22',
    title: 'TC22: Hỏi lại toàn bộ trước khi mua',
    description: 'Khách hàng chuẩn bị mua thì hỏi lại toàn bộ quyền lợi, thời hạn, giá cả',
    steps: [
        'Agent chào và giới thiệu',
        'Khách: "Tôi muốn mua, nhưng cho tôi hỏi lại"',
        'Agent sẵn sàng trả lời',
        'Khách hỏi: "Quyền lợi là gì?"',
        'Agent giải thích quyền lợi',
        'Khách hỏi: "Thời hạn đến bao lâu nữa phải mua tiếp?"',
        'Agent giải thích thời hạn 1 năm',
        'Khách hỏi: "Giá bao nhiêu?"',
        'Agent báo giá',
        'Khách: "Ok, rõ rồi, làm đi em"',
        'Agent cảm ơn'
    ],
    data: {
        title: 'anh',
        name: 'Trương Văn W',
        plate: '59D-22233',
        expire: '2024-09-20'
    },
    userMessages: [
        'Tôi muốn mua, nhưng cho tôi hỏi lại',
        'Quyền lợi là gì?',
        'Thời hạn đến bao lâu nữa phải mua tiếp?',
        'Giá bao nhiêu?',
        'Ok, rõ rồi, làm đi em'
    ],
    validations: [
        { type: 'greeting', keywords: ['xin chào', 'anh'] },
        { type: 'benefits', keywords: ['quyền lợi', 'bồi thường', 'bảo vệ'] },
        { type: 'duration', keywords: ['1 năm', 'thời hạn', '12 tháng'] },
        { type: 'price', keywords: ['giá', 'phí'] },
        { type: 'thanks', keywords: ['cảm ơn', 'anh'] }
    ]
};
