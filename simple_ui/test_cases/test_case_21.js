// TC21: Nhầm lẫn còn hạn, agent báo lại đúng
export const testCase21 = {
    id: 'tc21',
    title: 'TC21: Nhầm lẫn còn hạn BH',
    description: 'Khách hàng đang nhầm lẫn còn hạn, agent báo lại hạn đúng (đã hết lâu) => khách mua',
    steps: [
        'Agent chào và giới thiệu (BH đã hết hạn)',
        'Khách nói: "Tôi còn hạn mà, chưa cần đâu"',
        'Agent báo lại ngày hết hạn chính xác (đã hết lâu)',
        'Khách ngạc nhiên: "Ồ, tôi nhầm rồi"',
        'Agent khuyên nên mua ngay',
        'Khách: "Vậy làm luôn đi em"',
        'Agent cảm ơn'
    ],
    data: {
        title: 'chị',
        name: 'Võ Thị V',
        plate: '92F-11100',
        expire: '2023-12-10' // Đã hết hạn lâu
    },
    userMessages: [
        'Tôi còn hạn mà, chưa cần đâu',
        'Ồ, tôi nhầm rồi',
        'Vậy làm luôn đi em'
    ],
    validations: [
        { type: 'greeting', keywords: ['xin chào', 'chị'] },
        { type: 'expiry_correction', keywords: ['hết hạn', '10/12/2023', 'đã hết'] },
        { type: 'recommendation', keywords: ['mua', 'gia hạn', 'bảo hiểm'] },
        { type: 'thanks', keywords: ['cảm ơn', 'chị'] }
    ]
};
