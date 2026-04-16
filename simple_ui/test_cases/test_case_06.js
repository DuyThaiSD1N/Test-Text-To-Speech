// TC06: Hỏi giá nhiều lần rồi mua
export const testCase06 = {
    id: 'tc06',
    title: 'TC06: Hỏi giá nhiều lần rồi mua',
    description: 'Khách hàng hỏi giá chi tiết trước khi quyết định',
    steps: [
        'Agent chào và giới thiệu',
        'Khách hỏi: "Giá bao nhiêu vậy em?"',
        'Agent báo giá',
        'Khách hỏi: "Có rẻ hơn không?"',
        'Agent giải thích về giá và ưu đãi',
        'Khách đồng ý: "Được rồi, làm đi"',
        'Agent cảm ơn'
    ],
    data: {
        title: 'chị',
        name: 'Đỗ Thị F',
        plate: '43F-77777',
        expire: '2024-07-15'
    },
    userMessages: [
        'Giá bao nhiêu vậy em?',
        'Có rẻ hơn không?',
        'Được rồi, làm đi'
    ],
    validations: [
        { type: 'greeting', keywords: ['xin chào', 'chị'] },
        { type: 'price', keywords: ['giá', 'phí'] },
        { type: 'discount', keywords: ['giảm', 'ưu đãi', 'rẻ'] },
        { type: 'thanks', keywords: ['cảm ơn', 'chị'] }
    ]
};
