// TC05: Mua sau khi hiểu quyền lợi và bảo hiểm là gì
export const testCase05 = {
    id: 'tc05',
    title: 'TC05: Mua sau khi hiểu quyền lợi',
    description: 'Khách hàng hỏi về quyền lợi bảo hiểm và đồng ý mua',
    steps: [
        'Agent chào và giới thiệu',
        'Khách hỏi: "Bảo hiểm này có quyền lợi gì?"',
        'Agent giải thích quyền lợi bảo hiểm',
        'Khách hỏi tiếp: "Bảo hiểm là gì vậy em?"',
        'Agent giải thích về bảo hiểm',
        'Khách đồng ý: "À hiểu rồi, vậy làm đi em"',
        'Agent cảm ơn'
    ],
    data: {
        title: 'anh',
        name: 'Hoàng Văn E',
        plate: '92C-55555',
        expire: '2024-06-20'
    },
    userMessages: [
        'Bảo hiểm này có quyền lợi gì?',
        'Bảo hiểm là gì vậy em?',
        'À hiểu rồi, vậy làm đi em'
    ],
    validations: [
        { type: 'greeting', keywords: ['xin chào', 'anh'] },
        { type: 'benefits', keywords: ['quyền lợi', 'bồi thường', 'bảo vệ'] },
        { type: 'explanation', keywords: ['bảo hiểm', 'rủi ro', 'bảo vệ'] },
        { type: 'thanks', keywords: ['cảm ơn', 'anh'] }
    ]
};
