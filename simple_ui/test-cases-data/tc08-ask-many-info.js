// TC08: Khách hàng hỏi nhiều thông tin
const TC08 = {
    id: 'tc08',
    title: 'TC08: Hỏi nhiều thông tin',
    description: 'Khách hàng hỏi nhiều thông tin về bảo hiểm trước khi quyết định',
    steps: [
        'Agent chào và giới thiệu',
        'Khách hỏi: "Bảo hiểm này có những quyền lợi gì?"',
        'Agent giải thích quyền lợi',
        'Khách hỏi: "Giá bao nhiêu?"',
        'Agent báo giá',
        'Khách hỏi: "Thời hạn bao lâu?"',
        'Agent giải thích thời hạn',
        'Khách hỏi: "Có ưu đãi gì không?"',
        'Agent giới thiệu ưu đãi',
        'Khách đồng ý: "Ok, vậy làm đi em"',
        'Agent cảm ơn'
    ],
    data: {
        title: 'anh',
        name: 'Nguyễn Văn H',
        plate: '29B-11111',
        expire: '2024-09-10'
    },
    userMessages: [
        'Bảo hiểm này có những quyền lợi gì?',
        'Giá bao nhiêu?',
        'Thời hạn bao lâu?',
        'Có ưu đãi gì không?',
        'Ok, vậy làm đi em'
    ],
    validations: [
        { type: 'greeting', keywords: ['xin chào', 'anh'] },
        { type: 'benefits', keywords: ['quyền lợi', 'bồi thường'] },
        { type: 'price', keywords: ['giá', 'phí'] },
        { type: 'duration', keywords: ['thời hạn', 'năm'] },
        { type: 'promotion', keywords: ['ưu đãi', 'giảm'] },
        { type: 'thanks', keywords: ['cảm ơn', 'anh'] }
    ]
};
