// TC10: Khách hàng đã mua bảo hiểm nhưng vẫn muốn biết thông tin
const TC10 = {
    id: 'tc10',
    title: 'TC10: Đã mua nhưng hỏi thông tin',
    description: 'Khách hàng đã mua bảo hiểm nhưng vẫn muốn biết thêm thông tin',
    steps: [
        'Agent chào và giới thiệu',
        'Khách: "Tôi đã mua bảo hiểm rồi nhưng muốn hỏi thêm"',
        'Agent hỏi khách muốn biết gì',
        'Khách: "Quyền lợi cụ thể là gì?"',
        'Agent giải thích chi tiết quyền lợi',
        'Khách: "Cảm ơn em, tôi hiểu rồi"',
        'Agent cảm ơn và chào'
    ],
    data: {
        title: 'anh',
        name: 'Lê Văn J',
        plate: '30C-33333',
        expire: '2025-12-31' // Còn hạn dài
    },
    userMessages: [
        'Tôi đã mua bảo hiểm rồi nhưng muốn hỏi thêm',
        'Quyền lợi cụ thể là gì?',
        'Cảm ơn em, tôi hiểu rồi'
    ],
    validations: [
        { type: 'greeting', keywords: ['xin chào', 'anh'] },
        { type: 'benefits', keywords: ['quyền lợi', 'bồi thường', 'bảo vệ'] },
        { type: 'thanks', keywords: ['cảm ơn', 'anh'] }
    ]
};
