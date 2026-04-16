// TC17: Hỏi lỡ có tai nạn thì BH dùng như thế nào
export const testCase17 = {
    id: 'tc17',
    title: 'TC17: Hỏi cách dùng BH khi tai nạn',
    description: 'Khách hàng hỏi lỡ có tai nạn thì bảo hiểm dùng như thế nào, agent giải thích rồi khách mua',
    steps: [
        'Agent chào và giới thiệu',
        'Khách hỏi: "Lỡ có tai nạn thì bảo hiểm dùng như thế nào?"',
        'Agent giải thích quy trình bồi thường',
        'Khách hỏi: "Có phức tạp không?"',
        'Agent đảm bảo quy trình đơn giản',
        'Khách đồng ý: "Ok, vậy làm đi em"',
        'Agent cảm ơn'
    ],
    data: {
        title: 'chị',
        name: 'Hồ Thị Q',
        plate: '43C-11223',
        expire: '2024-05-20'
    },
    userMessages: [
        'Lỡ có tai nạn thì bảo hiểm dùng như thế nào?',
        'Có phức tạp không?',
        'Ok, vậy làm đi em'
    ],
    validations: [
        { type: 'greeting', keywords: ['xin chào', 'chị'] },
        { type: 'claim_process', keywords: ['tai nạn', 'bồi thường', 'quy trình'] },
        { type: 'simplicity', keywords: ['đơn giản', 'dễ', 'nhanh'] },
        { type: 'thanks', keywords: ['cảm ơn', 'chị'] }
    ]
};
