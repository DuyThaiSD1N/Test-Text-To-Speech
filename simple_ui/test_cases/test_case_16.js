// TC16: Còn hạn dài, agent báo giá thì khách bảo gửi thông tin
export const testCase16 = {
    id: 'tc16',
    title: 'TC16: Còn hạn dài - Gửi thông tin',
    description: 'Khách hàng chưa có ý định mua vì còn hạn dài, agent báo giá thì khách bảo gửi thông tin',
    steps: [
        'Agent chào và giới thiệu',
        'Khách nói: "Tôi còn hạn dài mà"',
        'Agent xác nhận và giới thiệu ưu đãi sớm',
        'Khách hỏi: "Giá bao nhiêu?"',
        'Agent báo giá',
        'Khách: "Để tôi nghĩ, em gửi thông tin cho tôi nhé"',
        'Agent đồng ý gửi thông tin và cảm ơn'
    ],
    data: {
        title: 'anh',
        name: 'Lâm Văn P',
        plate: '92E-99900',
        expire: '2025-06-15' // Còn hạn dài
    },
    userMessages: [
        'Tôi còn hạn dài mà',
        'Giá bao nhiêu?',
        'Để tôi nghĩ, em gửi thông tin cho tôi nhé'
    ],
    validations: [
        { type: 'greeting', keywords: ['xin chào', 'anh'] },
        { type: 'expiry_acknowledgment', keywords: ['còn hạn', '15/06/2025'] },
        { type: 'price', keywords: ['giá', 'phí'] },
        { type: 'send_info', keywords: ['gửi', 'thông tin', 'tin nhắn', 'dạ', 'vâng'] },
        { type: 'thanks', keywords: ['cảm ơn', 'anh', 'chúc', 'tốt lành'] }
    ]
};
