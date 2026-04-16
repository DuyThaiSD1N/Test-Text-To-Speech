// TC09: Khách hàng chưa rõ thời hạn bảo hiểm
const TC09 = {
    id: 'tc09',
    title: 'TC09: Chưa rõ thời hạn BH',
    description: 'Khách hàng chưa rõ thời hạn, sau khi biết gần hết hạn thì mua',
    steps: [
        'Agent chào và giới thiệu (bảo hiểm hết hạn 15/03/2024)',
        'Khách hỏi: "Bảo hiểm của tôi còn hạn bao lâu?"',
        'Agent thông báo đã hết hạn từ 15/03/2024',
        'Khách: "À, vậy tôi cần mua lại rồi"',
        'Agent xác nhận và hỏi loại xe',
        'Khách: "Xe máy"',
        'Agent cảm ơn'
    ],
    data: {
        title: 'chị',
        name: 'Trần Thị I',
        plate: '51C-22222',
        expire: '2024-03-15' // Đã hết hạn
    },
    userMessages: [
        'Bảo hiểm của tôi còn hạn bao lâu?',
        'À, vậy tôi cần mua lại rồi',
        'Xe máy'
    ],
    validations: [
        { type: 'greeting', keywords: ['xin chào', 'chị'] },
        { type: 'expiry_info', keywords: ['15/03/2024', 'hết hạn'] },
        { type: 'thanks', keywords: ['cảm ơn', 'chị'] }
    ]
};
