// TC03: Mua ngay từ đầu - Agent hỏi loại xe
export const testCase03 = {
    id: 'tc03',
    title: 'TC03: Mua ngay từ đầu',
    description: 'Khách hàng đồng ý mua ngay, agent hỏi loại xe',
    steps: [
        'Agent chào và giới thiệu',
        'Khách đồng ý ngay: "Được, làm đi em"',
        'Agent hỏi loại xe',
        'Khách trả lời: "Xe máy"',
        'Agent cảm ơn'
    ],
    data: {
        title: 'anh',
        name: 'Lê Văn C',
        plate: '30H-11111',
        expire: '2024-02-20'
    },
    userMessages: [
        'Được, làm đi em',
        'Xe máy'
    ],
    validations: [
        { type: 'greeting', keywords: ['xin chào', 'anh'] },
        { type: 'vehicle_question', keywords: ['loại xe', 'xe gì', 'xe nào'] },
        { type: 'thanks', keywords: ['cảm ơn', 'anh'] }
    ]
};
