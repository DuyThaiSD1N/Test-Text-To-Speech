// TC13: Từ chối nhưng agent báo ưu đãi thì quay đầu
export const testCase13 = {
    id: 'tc13',
    title: 'TC13: Từ chối rồi quay đầu mua',
    description: 'Khách hàng từ chối, agent báo ưu đãi rồi khách hàng quay đầu muốn mua',
    steps: [
        'Agent chào và giới thiệu',
        'Khách từ chối: "Không cần, tôi không quan tâm"',
        'Agent giới thiệu ưu đãi đặc biệt (giảm 20% + tặng thêm)',
        'Khách quan tâm: "Ưu đãi thế à?"',
        'Agent xác nhận và giải thích thêm',
        'Khách đổi ý: "Vậy làm đi em"',
        'Agent cảm ơn'
    ],
    data: {
        title: 'chị',
        name: 'Mai Thị M',
        plate: '88D-33344',
        expire: '2024-03-25'
    },
    userMessages: [
        'Không cần, tôi không quan tâm',
        'Ưu đãi thế à?',
        'Vậy làm đi em'
    ],
    validations: [
        { type: 'greeting', keywords: ['xin chào', 'chị'] },
        { type: 'rejection_handling', keywords: ['không cần', 'không quan tâm'] },
        { type: 'promotion', keywords: ['ưu đãi', 'giảm', '20%', 'tặng'] },
        { type: 'thanks', keywords: ['cảm ơn', 'chị'] }
    ]
};
