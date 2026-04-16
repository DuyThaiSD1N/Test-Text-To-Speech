// TC15: Không quan tâm nhưng nghe lợi ích thì đổi ý
export const testCase15 = {
    id: 'tc15',
    title: 'TC15: Không quan tâm rồi đổi ý',
    description: 'Khách hàng nói không quan tâm, agent bảo không có BH thì rủi ro + ưu đãi => khách đổi ý',
    steps: [
        'Agent chào và giới thiệu',
        'Khách nói: "Tôi không quan tâm"',
        'Agent giải thích rủi ro khi không có bảo hiểm',
        'Khách hỏi: "Rủi ro gì?"',
        'Agent giải thích chi tiết + mua bây giờ có ưu đãi',
        'Khách đổi ý: "Vậy làm đi em"',
        'Agent cảm ơn'
    ],
    data: {
        title: 'chị',
        name: 'Đinh Thị O',
        plate: '59A-77788',
        expire: '2024-03-30'
    },
    userMessages: [
        'Tôi không quan tâm',
        'Rủi ro gì?',
        'Vậy làm đi em'
    ],
    validations: [
        { type: 'greeting', keywords: ['xin chào', 'chị'] },
        { type: 'rejection', keywords: ['không quan tâm'] },
        { type: 'risk_explanation', keywords: ['rủi ro', 'tai nạn', 'bồi thường'] },
        { type: 'promotion', keywords: ['ưu đãi', 'giảm'] },
        { type: 'thanks', keywords: ['cảm ơn', 'chị'] }
    ]
};
