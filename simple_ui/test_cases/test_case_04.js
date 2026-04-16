// TC04: Mua sau khi nghe ưu đãi
export const testCase04 = {
    id: 'tc04',
    title: 'TC04: Mua sau khi nghe ưu đãi',
    description: 'Khách hàng quan tâm ưu đãi và quyết định mua',
    steps: [
        'Agent chào và giới thiệu',
        'Khách hỏi: "Có ưu đãi gì không em?"',
        'Agent giới thiệu ưu đãi giảm 20%, tặng bảo hiểm tai nạn',
        'Khách đồng ý: "Ưu đãi tốt đấy, làm luôn"',
        'Agent cảm ơn'
    ],
    data: {
        title: 'chị',
        name: 'Phạm Thị D',
        plate: '59B-33333',
        expire: '2024-05-10'
    },
    userMessages: [
        'Có ưu đãi gì không em?',
        'Ưu đãi tốt đấy, làm luôn'
    ],
    validations: [
        { type: 'greeting', keywords: ['xin chào', 'chị'] },
        { type: 'promotion', keywords: ['giảm', '20%', 'ưu đãi', 'tai nạn'] },
        { type: 'thanks', keywords: ['cảm ơn', 'chị'] }
    ]
};
