import torch
import torch.nn as nn
import pickle
import numpy as np


labels = ['Time Interval Query', 'Time Point Query', 'Spatial Range Query', 'Time Range Query', \
          'Spatio-temporal Range Query', 'Spatial Nearest Neighbor Query', 'Moving Objects Nearest Neighbor Query', \
          'Spatial Join Query', 'Spatio-temporal Join Query', 'Similarity Query', 'Spatial Basic-distance Query', \
          'Spatial Basic-direction Query', 'Spatial Basic-length Query', 'Spatial Basic-area Query', 'Spatial Aggregation-count Query', \
          'Spatial Aggregation-sum Query', 'Spatial Aggregation-max Query', 'Temporal Aggregation Query', 'Normal Basic Query']

# 定义LSTMCNN模型
class LSTMCNN(nn.Module):
    def __init__(self, num_embeddings, embedding_size, hidden_size, num_classes, num_filters=100, kernel_sizes=[3,4,5]):
        super(LSTMCNN, self).__init__()
        self.embedding = nn.Embedding(num_embeddings, embedding_size)
        self.lstm = nn.LSTM(input_size=embedding_size, hidden_size=hidden_size, bidirectional=True, batch_first=True)
        self.convolution_layers = nn.ModuleList([
            nn.Conv1d(in_channels=2*hidden_size, out_channels=num_filters, kernel_size=kernel_size)
            for kernel_size in kernel_sizes
        ])
        self.dropout = nn.Dropout(0.5)
        self.linear = nn.Linear(len(kernel_sizes) * num_filters, num_classes)

    def forward(self, x):
        x = self.embedding(x)
        lstm_output, (h_n, c_n) = self.lstm(x)
        x = lstm_output.permute(0, 2, 1)
        convolution_outputs = []
        for convolution in self.convolution_layers:
            convolution_output = convolution(x)
            convolution_output = nn.functional.relu(convolution_output)
            max_pool_output = nn.functional.max_pool1d(convolution_output, kernel_size=convolution_output.size(2))
            convolution_outputs.append(max_pool_output)
        concatenated_tensor = torch.cat(convolution_outputs, dim=1)
        flatten_tensor = concatenated_tensor.view(concatenated_tensor.size(0), -1)
        dropout_output = self.dropout(flatten_tensor)
        logits = self.linear(dropout_output)
        return logits


# 加载模型和相关信息
word_to_idx = torch.load('word_to_idx.pth')
max_length = torch.load('max_length.pth')
num_classes = len(labels)
model = LSTMCNN(len(word_to_idx), embedding_size=200, hidden_size=128, num_classes=num_classes, num_filters=200, kernel_sizes=[3,4,5])
model.load_state_dict(torch.load('model.pth'))
model.eval()


def predict_type(text):
    # 将文本转换为Tensor
    vector = np.array([word_to_idx.get(word, 1) for word in text.split()] + [0]*(max_length-len(text.split())))
    vector_tensor = torch.LongTensor(vector).unsqueeze(0)
    # 对文本进行分类预测
    with torch.no_grad():
        logits = model(vector_tensor)
        predicted_class = torch.argmax(logits, dim=1).item()
    # 返回预测结果
    return labels[predicted_class]


# 测试预测函数
# print("T1")
# print(predict_type('What are the kinos in thecenter?'))
# print(predict_type('List all wstrassens that intersect the mrainline.'))
# print(predict_type('Show me some trajectories of some taxies.'))
print( predict_type('Where were the trains between 7:00am and 8:00am?'))
# print("T2")
# print(predict_type('What is the nearest gas station from here?'))
# print(predict_type('Find the 13 nearest kneipen to the flaechen named Viktoriapark?'))
# print("T3")
# print(predict_type('What sehenswuerdregs are these restaurants located in?'))
# print(predict_type('In each sehenswuerdreg, list the details of the kinos.'))
# print("T4")
# print(predict_type('What kinos are within 1.5 kilometers of each Flaechen?'))
# print("T5")
# print(predict_type('How many kinos are in each Flaechen?'))
# print(predict_type('How many strassens does each RBahn intersect?'))
# print("T6")
# print(predict_type('What is the total area where TreptowerPark and WFlaechen intersect?'))
# print(predict_type('What is the total area where koepenick and WFlaechen intersect?'))
# print("T7")
# print(predict_type('Please list the Flaechen that contains the most kinos.'))
# print(predict_type('Which WFlaechen has the largest area of intersection with TreptowerPark?'))
# print("T8")
# print(predict_type('Returns the distance between mehringdamm and alexanderplatz'))
# print("T9")
# print(predict_type('Return to the direction from mehringdamm to alexanderplatz'))
# print("T10")
# print(predict_type('Returns the length of PotsdamLine'))
# print("T11")
# print(predict_type("Area of Li River?"))
# print(predict_type('Returns the type of a UBahn named U7'))

