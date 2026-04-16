// TC02: Bảo hiểm ô tô - Khách hỏi giá và mua
export const testCase02 = {
    id: 'tc02',
    title: 'TC02: Bảo hiểm ô tô',
    description: 'Khách hàng hỏi về xe ô tô và đồng ý mua',
    steps: [
        'Agent chào và giới thiệu (đã biết ô tô)',
        'Khách hỏi: "Xe ô tô giá bao nhiêu?"',
        'Agent báo giá 400-600k (không hỏi loại xe)',
        'Khách đồng ý: "Ok, làm luôn"',
        'Agent cảm ơn'
    ],
    data: {
        title: 'chị',
        name: 'Trần Thị B',
        vehicleType: 'ô tô',
        plate: '51G-67890',
        expire: '2024-04-01'
    },
    userMessages: [
        'Xe ô tô giá bao nhiêu?',
        'Ok, làm luôn'
    ],
    validations: [
        { type: 'greeting', keywords: ['xin chào', 'chị', '51G-67890', 'ô tô'] },
        { type: 'price', keywords: ['400', '600'] },
        { type: 'no_vehicle_question', keywords: [] }, // Không hỏi loại xe
        { type: 'thanks', keywords: ['cảm ơn', 'chị'] }
    ]
};
