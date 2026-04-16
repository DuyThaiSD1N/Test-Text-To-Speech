// TC09: Chưa rõ thời hạn, sau khi biết gần hết hạn thì mua
export const testCase09 = {
    id: 'tc09',
    title: 'TC09: Chưa rõ thời hạn BH',
    description: 'Khách hàng chưa rõ thời hạn bảo hiểm, sau khi biết gần hết/hết hạn thì mua',
    steps: [
        'Agent chào và giới thiệu (có thông tin hết hạn)',
        'Khách hỏi: "Bảo hiểm của tôi hết hạn khi nào?"',
        'Agent báo ngày hết hạn (đã hết hoặc sắp hết)',
        'Khách ngạc nhiên: "Ồ, vậy à? Tôi không biết"',
        'Agent khuyên nên gia hạn',
        'Khách đồng ý: "Vậy làm luôn đi em"',
        'Agent cảm ơn'
    ],
    data: {
        title: 'chị',
        name: 'Ngô Thị I',
        plate: '51B-44444',
        expire: '2024-01-05' // Đã hết hạn
    },
    userMessages: [
        'Bảo hiểm của tôi hết hạn khi nào?',
        'Ồ, vậy à? Tôi không biết',
        'Vậy làm luôn đi em'
    ],
    validations: [
        { type: 'greeting', keywords: ['xin chào', 'chị'] },
        { type: 'expiry_info', keywords: ['hết hạn', '05/01/2024'] },
        { type: 'recommendation', keywords: ['gia hạn', 'mua', 'bảo hiểm'] },
        { type: 'thanks', keywords: ['cảm ơn', 'chị'] }
    ]
};
