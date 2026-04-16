// TC01: Bảo hiểm xe máy - Khách hỏi giá và mua
export const testCase01 = {
    id: 'tc01',
    title: 'TC01: Bảo hiểm xe máy',
    description: 'Khách hàng hỏi giá và đồng ý mua bảo hiểm xe máy',
    steps: [
        'Agent chào và giới thiệu (đã biết xe máy)',
        'Khách hỏi: "Xe máy giá bao nhiêu?"',
        'Agent báo giá 100-150k (không hỏi loại xe)',
        'Khách đồng ý: "Ok, làm luôn"',
        'Agent cảm ơn'
    ],
    data: {
        title: 'anh',
        name: 'Nguyễn Văn A',
        vehicleType: 'xe máy',
        plate: '29A-12345',
        expire: '2024-03-15'
    },
    userMessages: [
        'Xe máy giá bao nhiêu?',
        'Ok, làm luôn'
    ],
    validations: [
        { type: 'greeting', keywords: ['xin chào', 'anh', '29A-12345', 'xe máy'] },
        { type: 'price', keywords: ['100', '150'] },
        { type: 'no_vehicle_question', keywords: [] }, // Không hỏi loại xe
        { type: 'thanks', keywords: ['cảm ơn', 'anh'] }
    ]
};
