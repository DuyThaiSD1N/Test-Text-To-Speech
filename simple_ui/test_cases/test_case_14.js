// TC14: Giá đắt, từ chối nhưng nghe ưu đãi thì đổi ý
export const testCase14 = {
    id: 'tc14',
    title: 'TC14: Giá đắt nhưng có ưu đãi',
    description: 'Khách hàng sau khi nghe giá đắt, từ chối nhưng agent báo ưu đãi thì đổi ý mua',
    steps: [
        'Agent chào và giới thiệu',
        'Khách hỏi: "Giá bao nhiêu?"',
        'Agent báo giá',
        'Khách phản ứng: "Đắt quá, thôi không cần"',
        'Agent giới thiệu ưu đãi giảm giá đặc biệt',
        'Khách đổi ý: "Vậy được, làm đi"',
        'Agent cảm ơn'
    ],
    data: {
        title: 'anh',
        name: 'Cao Văn N',
        plate: '30B-55566',
        expire: '2024-04-10'
    },
    userMessages: [
        'Giá bao nhiêu?',
        'Đắt quá, thôi không cần',
        'Vậy được, làm đi'
    ],
    validations: [
        { type: 'greeting', keywords: ['xin chào', 'anh'] },
        { type: 'price', keywords: ['giá', 'phí'] },
        { type: 'rejection', keywords: ['đắt', 'không cần'] },
        { type: 'promotion', keywords: ['ưu đãi', 'giảm'] },
        { type: 'thanks', keywords: ['cảm ơn', 'anh'] }
    ]
};
