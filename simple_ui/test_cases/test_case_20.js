// TC20: Muốn mua nhưng để tên người khác
export const testCase20 = {
    id: 'tc20',
    title: 'TC20: Mua để tên người khác',
    description: 'Khách hàng muốn mua nhưng để tên người khác',
    steps: [
        'Agent chào và giới thiệu',
        'Khách hỏi: "Tôi muốn mua nhưng để tên người khác được không?"',
        'Agent xác nhận được và hỏi thông tin',
        'Khách: "Để tên vợ tôi, tên Nguyễn Thị T"',
        'Agent xác nhận và hỏi thêm thông tin cần thiết',
        'Khách: "Ok, làm đi em"',
        'Agent cảm ơn'
    ],
    data: {
        title: 'anh',
        name: 'Phạm Văn U',
        plate: '30C-88899',
        expire: '2024-08-15'
    },
    userMessages: [
        'Tôi muốn mua nhưng để tên người khác được không?',
        'Để tên vợ tôi, tên Nguyễn Thị T',
        'Ok, làm đi em'
    ],
    validations: [
        { type: 'greeting', keywords: ['xin chào', 'anh'] },
        { type: 'different_name', keywords: ['tên người khác', 'được', 'tên vợ'] },
        { type: 'confirmation', keywords: ['Nguyễn Thị T', 'xác nhận'] },
        { type: 'thanks', keywords: ['cảm ơn', 'anh'] }
    ]
};
