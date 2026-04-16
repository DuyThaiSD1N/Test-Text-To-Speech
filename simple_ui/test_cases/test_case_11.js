// TC11: Đã mua BH nhưng sắp hết hạn + nghe ưu đãi thì mua
export const testCase11 = {
    id: 'tc11',
    title: 'TC11: Đã mua BH sắp hết hạn',
    description: 'Khách hàng đã mua bảo hiểm nhưng sắp hết hạn, nghe ưu đãi thì mua',
    steps: [
        'Agent chào và giới thiệu (BH sắp hết hạn)',
        'Khách nói: "Tôi đã mua bảo hiểm rồi mà"',
        'Agent thông báo sắp hết hạn và có ưu đãi gia hạn',
        'Khách hỏi: "Ưu đãi gì?"',
        'Agent giới thiệu ưu đãi giảm 20%',
        'Khách đồng ý: "Ưu đãi tốt đấy, làm luôn"',
        'Agent cảm ơn'
    ],
    data: {
        title: 'chị',
        name: 'Lý Thị K',
        plate: '43G-88888',
        expire: '2024-04-20' // Sắp hết hạn
    },
    userMessages: [
        'Tôi đã mua bảo hiểm rồi mà',
        'Ưu đãi gì?',
        'Ưu đãi tốt đấy, làm luôn'
    ],
    validations: [
        { type: 'greeting', keywords: ['xin chào', 'chị'] },
        { type: 'expiry_reminder', keywords: ['sắp hết', 'hết hạn', '20/04/2024'] },
        { type: 'promotion', keywords: ['ưu đãi', 'giảm', '20%'] },
        { type: 'thanks', keywords: ['cảm ơn', 'chị'] }
    ]
};
