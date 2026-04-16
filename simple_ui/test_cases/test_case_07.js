// TC07: Hỏi nguồn thông tin rồi tin tưởng
export const testCase07 = {
    id: 'tc07',
    title: 'TC07: Hỏi nguồn thông tin rồi tin tưởng',
    description: 'Khách hàng thắc mắc về nguồn thông tin, agent giải thích và khách tin tưởng',
    steps: [
        'Agent chào và giới thiệu',
        'Khách hỏi: "Sao em biết thông tin của tôi?"',
        'Agent giải thích về nguồn dữ liệu hợp pháp',
        'Khách hỏi: "Vậy có an toàn không?"',
        'Agent đảm bảo về bảo mật thông tin',
        'Khách tin tưởng: "Được, tôi tin em, làm đi"',
        'Agent cảm ơn'
    ],
    data: {
        title: 'anh',
        name: 'Vũ Văn G',
        plate: '88H-99999',
        expire: '2024-08-25'
    },
    userMessages: [
        'Sao em biết thông tin của tôi?',
        'Vậy có an toàn không?',
        'Được, tôi tin em, làm đi'
    ],
    validations: [
        { type: 'greeting', keywords: ['xin chào', 'anh'] },
        { type: 'data_source', keywords: ['dữ liệu', 'hợp pháp', 'cơ quan'] },
        { type: 'security', keywords: ['an toàn', 'bảo mật', 'bảo vệ'] },
        { type: 'thanks', keywords: ['cảm ơn', 'anh'] }
    ]
};
