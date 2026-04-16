// TC18: Hỏi về tính uy tín, thực tế của bảo hiểm
export const testCase18 = {
    id: 'tc18',
    title: 'TC18: Hỏi về uy tín BH',
    description: 'Khách hàng hỏi về tính uy tín, thực tế của bảo hiểm',
    steps: [
        'Agent chào và giới thiệu',
        'Khách hỏi: "Bảo hiểm này có uy tín không?"',
        'Agent giải thích về công ty và uy tín',
        'Khách hỏi: "Có thực tế bồi thường không?"',
        'Agent đảm bảo và đưa ra ví dụ thực tế',
        'Khách: "Ok, tôi hiểu rồi, cảm ơn em"',
        'Agent cảm ơn'
    ],
    data: {
        title: 'anh',
        name: 'Đặng Văn R',
        plate: '88C-44455',
        expire: '2024-06-25'
    },
    userMessages: [
        'Bảo hiểm này có uy tín không?',
        'Có thực tế bồi thường không?',
        'Ok, tôi hiểu rồi, cảm ơn em'
    ],
    validations: [
        { type: 'greeting', keywords: ['xin chào', 'anh'] },
        { type: 'credibility', keywords: ['uy tín', 'công ty', 'tin cậy'] },
        { type: 'real_cases', keywords: ['thực tế', 'bồi thường', 'khách hàng'] },
        { type: 'thanks', keywords: ['cảm ơn', 'anh'] }
    ]
};
