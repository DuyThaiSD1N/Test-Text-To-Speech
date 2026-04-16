// TC12: Muốn đổi sang nhà cung cấp mới có ưu đãi
export const testCase12 = {
    id: 'tc12',
    title: 'TC12: Đổi nhà cung cấp mới',
    description: 'Khách hàng dùng xe máy, muốn đổi sang nhà cung cấp mới có ưu đãi',
    steps: [
        'Agent chào và giới thiệu',
        'Khách hỏi: "Tôi đang dùng nhà khác, có lợi gì khi chuyển sang?"',
        'Agent giới thiệu ưu đãi và quyền lợi tốt hơn, hỏi loại xe',
        'Khách trả lời: "Xe máy"',
        'Agent báo giá xe máy + ưu đãi giảm 20%',
        'Khách hỏi: "Giá có rẻ hơn không?"',
        'Agent xác nhận giá cạnh tranh với ưu đãi',
        'Khách đồng ý: "Ok, tôi chuyển sang"',
        'Agent cảm ơn'
    ],
    data: {
        title: 'anh',
        name: 'Phan Văn L',
        plate: '59C-11122',
        expire: '2024-05-15'
    },
    userMessages: [
        'Tôi đang dùng nhà khác, có lợi gì khi chuyển sang?',
        'Xe máy',
        'Giá có rẻ hơn không?',
        'Ok, tôi chuyển sang'
    ],
    validations: [
        { type: 'greeting', keywords: ['xin chào', 'anh'] },
        { type: 'benefits', keywords: ['quyền lợi', 'ưu đãi', 'tốt hơn'] },
        { type: 'vehicle_question', keywords: ['loại xe', 'xe gì', 'xe nào'] },
        { type: 'price', keywords: ['giá', '100', '150', 'xe máy'] },
        { type: 'discount', keywords: ['giảm', '20%', 'ưu đãi'] },
        { type: 'thanks', keywords: ['cảm ơn', 'anh'] }
    ]
};
