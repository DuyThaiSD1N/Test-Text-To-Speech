// TC10: Đã mua BH nhưng vẫn muốn biết thông tin
export const testCase10 = {
    id: 'tc10',
    title: 'TC10: Đã mua BH nhưng muốn biết thêm',
    description: 'Khách hàng đã mua bảo hiểm nhưng vẫn muốn biết thông tin',
    steps: [
        'Agent chào và giới thiệu',
        'Khách nói: "Tôi đã mua bảo hiểm rồi"',
        'Agent hỏi thêm về nhu cầu',
        'Khách hỏi: "Tôi muốn biết quyền lợi cụ thể"',
        'Agent giải thích chi tiết quyền lợi',
        'Khách: "Ok, cảm ơn em nhé"',
        'Agent cảm ơn và chào'
    ],
    data: {
        title: 'anh',
        name: 'Trịnh Văn J',
        plate: '92D-66666',
        expire: '2025-12-30' // Còn hạn dài
    },
    userMessages: [
        'Tôi đã mua bảo hiểm rồi',
        'Tôi muốn biết quyền lợi cụ thể',
        'Ok, cảm ơn em nhé'
    ],
    validations: [
        { type: 'greeting', keywords: ['xin chào', 'anh'] },
        { type: 'acknowledgment', keywords: ['đã mua', 'rồi'] },
        { type: 'benefits', keywords: ['quyền lợi', 'bồi thường', 'bảo vệ'] },
        { type: 'thanks', keywords: ['cảm ơn', 'anh'] }
    ]
};
