// TC19: Hỏi về cách đóng tiền (chuyển khoản / trực tiếp)
export const testCase19 = {
    id: 'tc19',
    title: 'TC19: Hỏi cách đóng tiền',
    description: 'Khách hàng có thắc mắc về cách đóng tiền, agent cho 2 lựa chọn',
    steps: [
        'Agent chào và giới thiệu',
        'Khách hỏi: "Đóng tiền như thế nào?"',
        'Agent giải thích 2 cách: chuyển khoản hoặc trực tiếp',
        'Khách hỏi: "Chuyển khoản thì sao?"',
        'Agent: Sẽ nhắn tin thông tin tài khoản',
        'Khách: "Ok, vậy làm đi, tôi chuyển khoản"',
        'Agent cảm ơn và hẹn gửi thông tin'
    ],
    data: {
        title: 'chị',
        name: 'Lưu Thị S',
        plate: '51D-66677',
        expire: '2024-07-30'
    },
    userMessages: [
        'Đóng tiền như thế nào?',
        'Chuyển khoản thì sao?',
        'Ok, vậy làm đi, tôi chuyển khoản'
    ],
    validations: [
        { type: 'greeting', keywords: ['xin chào', 'chị'] },
        { type: 'payment_methods', keywords: ['chuyển khoản', 'trực tiếp', 'đóng tiền'] },
        { type: 'transfer_info', keywords: ['nhắn tin', 'thông tin', 'tài khoản'] },
        { type: 'thanks', keywords: ['cảm ơn', 'chị'] }
    ]
};
