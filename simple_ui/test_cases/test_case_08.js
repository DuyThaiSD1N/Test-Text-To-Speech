// TC08: Hỏi nhiều thông tin trước khi quyết định
export const testCase08 = {
    id: 'tc08',
    title: 'TC08: Hỏi nhiều thông tin',
    description: 'Khách hàng hỏi nhiều thông tin chi tiết trước khi mua',
    steps: [
        'Agent chào và giới thiệu',
        'Khách hỏi: "Bảo hiểm này bao gồm những gì?"',
        'Agent giải thích chi tiết',
        'Khách hỏi: "Giá bao nhiêu?"',
        'Agent báo giá',
        'Khách hỏi: "Có ưu đãi gì không?"',
        'Agent giới thiệu ưu đãi',
        'Khách đồng ý: "Ok, làm đi em"',
        'Agent cảm ơn'
    ],
    data: {
        title: 'anh',
        name: 'Bùi Văn H',
        plate: '30A-22222',
        expire: '2024-09-10'
    },
    userMessages: [
        'Bảo hiểm này bao gồm những gì?',
        'Giá bao nhiêu?',
        'Có ưu đãi gì không?',
        'Ok, làm đi em'
    ],
    validations: [
        { type: 'greeting', keywords: ['xin chào', 'anh'] },
        { type: 'coverage', keywords: ['bao gồm', 'quyền lợi', 'bảo vệ'] },
        { type: 'price', keywords: ['giá', 'phí'] },
        { type: 'promotion', keywords: ['ưu đãi', 'giảm'] },
        { type: 'thanks', keywords: ['cảm ơn', 'anh'] }
    ]
};
