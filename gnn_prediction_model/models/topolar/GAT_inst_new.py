import torch
import torch.nn.functional as F
from torch_geometric.nn import GATConv, JumpingKnowledge, global_mean_pool, SAGEConv, GCNConv
from torch_geometric.loader import DataLoader
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score, roc_auc_score
import logging
import argparse
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error
from torch.nn import Linear, ModuleList, BatchNorm1d
import numpy as np

# Assuming GNNDataset_criticalpath is already defined as per your provided script
from get_dataset import GNNDataset_criticalpath

class SAGE_JK(torch.nn.Module):
    def __init__(self, num_node_features, conv_neurons, conv_type='GAT', num_layers=3):
        super(SAGE_JK, self).__init__()

        # 设置跳跃知识的模式
        jk_mode = 'cat'
        
        # 定义卷积层类型的字典
        conv_dict = {
            'GCN': GCNConv,
            'GAT': GATConv,
            'SAGE': SAGEConv
        }

        # 初始化卷积层和批归一化层
        self.convs = ModuleList()
        self.bns = ModuleList()

        for i in range(num_layers):
            in_channels = num_node_features if i == 0 else conv_neurons
            self.convs.append(conv_dict[conv_type](in_channels, conv_neurons))
            self.bns.append(BatchNorm1d(conv_neurons))
        
        # 初始化跳跃知识层
        self.jk = JumpingKnowledge(mode=jk_mode, channels=conv_neurons, num_layers=num_layers)
        
        # 计算拼接后的特征大小
        concatenated_feature_size = conv_neurons * num_layers if jk_mode == 'cat' else conv_neurons
        
        # 初始化分类用的全连接层
        self.lin1 = torch.nn.Linear(concatenated_feature_size, conv_neurons * 2)
        self.lin2 = torch.nn.Linear(conv_neurons * 2, conv_neurons // 2)
        self.lin3 = torch.nn.Linear(conv_neurons // 2, 1)

        # 初始化回归用的全连接层
        self.reg_lin1 = torch.nn.Linear(17 + concatenated_feature_size + 1, 32)  # 加上170和池化后的特征
        self.reg_lin2 = torch.nn.Linear(32, 1)  # 回归输出为1维


    def forward(self, data):  
        x, edge_index, batch = data.x, data.edge_index, data.batch
        layer_features = []
        
        delay_param = data.x[:, 0]
        # print(delay_param)

        for conv, bn in zip(self.convs, self.bns):
            x = conv(x, edge_index)
            x = bn(x)
            x = F.relu(x)
            x = F.dropout(x, training=self.training)
            layer_features.append(x)
        
        x = self.jk(layer_features)

        # Classification output: 对每个节点进行预测
        node_output = F.relu(self.lin1(x))
        node_output = F.relu(self.lin2(node_output))
        node_output = self.lin3(node_output)

        node_delay = node_output * delay_param.view(-1, 1)

        # 对每个图的节点进行全局池化
        x_class = global_mean_pool(node_delay, batch)  # 池化的是node_output
        x_pool = global_mean_pool(x, batch)  # 池化x以获取图的特征

        # Regression output
        other_attrs = data.other_attrs.view(-1, 18)  # 确保other_attrs是合适的形状

        # print("Shape of other_attrs:", other_attrs.shape)
        # 选取前170个属性
        reg_input = other_attrs[:, :17]  # Shape: [batch_size, 170]

        # print("Shape of reg_input:", reg_input.shape)  # 应该是 [batch_size, 170]
        # print("Shape of x_class:", x_class.shape)  # 确保 x_class 的形状与 reg_input 相匹配
        # print("Shape of x_pool:", x_pool.shape)  # 确保池化后的x的形状

        # 使用last_attr（最后一个属性）作为真实值标签
        last_attr = other_attrs[:, -1].unsqueeze(1)  # Shape: [batch_size, 1]

        # 合并reg_input、x_class（池化后的node_output）和x_pool（池化后的x）
        reg_input = torch.cat((reg_input, x_class, x_pool), dim=1)  # Shape: [batch_size, 170 + 特征维度]
        print()

        # 回归输出
        reg_output = F.relu(self.reg_lin1(reg_input))
        reg_output = self.reg_lin2(reg_output)

        return node_output, reg_output, last_attr  # 返回last_attr以便于计算误差

def train(train_loader):
    model.train()
    total_loss = 0
    total_node_loss = 0
    total_reg_loss = 0
    total_mape = 0
    all_reg_preds = []
    all_reg_labels = []

    for data in train_loader:
        data = data.to(device)
        optimizer.zero_grad()

        node_output, reg_output, last_attr = model(data)

        node_loss = F.mse_loss(node_output.view_as(data.y).float(), data.y.float())  # 确保维度匹配
        # 计算回归损失
        reg_loss = F.mse_loss(reg_output.squeeze(), last_attr.squeeze())  # 确保维度匹配
        loss = node_loss + 100 * reg_loss  # Total loss

        loss.backward()
        optimizer.step()

        total_loss += loss.item() * data.num_graphs
        total_node_loss += node_loss.item() * data.num_graphs
        total_reg_loss += reg_loss.item() * data.num_graphs

        all_reg_preds.extend(reg_output.detach().cpu().numpy())
        all_reg_labels.extend(last_attr.detach().cpu().numpy())

        # 计算 MAPE
        mape = torch.mean(torch.abs((reg_output.squeeze() - last_attr) / last_attr)) * 100  # MAPE 计算
        total_mape += mape.item() * data.num_graphs

    average_loss = total_loss / len(train_loader.dataset)
    average_node_loss = total_node_loss / len(train_loader.dataset)  # 平均节点损失
    average_reg_loss = total_reg_loss / len(train_loader.dataset)
    average_mape = total_mape / len(train_loader.dataset)  # 平均 MAPE

    # 计算相关系数 R
    all_reg_preds_np = np.array(all_reg_preds)
    all_reg_labels_np = np.array(all_reg_labels)
    correlation_matrix = np.corrcoef(all_reg_labels_np.flatten(), all_reg_preds_np.flatten())
    correlation_coefficient = correlation_matrix[0, 1]

    # 计算 RRSE
    rrse = np.sqrt(mean_squared_error(all_reg_labels_np.flatten(), all_reg_preds_np).flatten() / np.var(all_reg_labels_np)).item()

    return average_loss, average_node_loss, average_reg_loss, average_mape, correlation_coefficient, rrse

def test(data_loader):
    model.eval()
    total_loss = 0
    total_node_loss = 0
    total_reg_loss = 0
    total_mape = 0
    all_preds = []
    all_labels = []
    all_reg_preds = []
    all_reg_labels = []

    with torch.no_grad():
        for data in data_loader:
            data = data.to(device)

            node_output, reg_output, last_attr = model(data)

            node_loss = F.mse_loss(node_output.view_as(data.y).float(), data.y.float())  # 确保维度匹配
            # 计算回归损失
            reg_loss = F.mse_loss(reg_output.squeeze(), last_attr.squeeze())  # 确保维度匹配
            loss = node_loss + 100 * reg_loss  # Total loss

            total_loss += loss.item() * data.num_graphs
            total_node_loss += node_loss.item() * data.num_graphs
            total_reg_loss += reg_loss.item() * data.num_graphs
            
            all_preds.extend(node_output.cpu().numpy())
            all_labels.extend(data.y.cpu().numpy())
            all_reg_preds.extend(reg_output.cpu().numpy())
            all_reg_labels.extend(last_attr.cpu().numpy())

            # 计算 MAPE
            mape = torch.mean(torch.abs((reg_output.squeeze() - last_attr) / last_attr)) * 100  # MAPE 计算
            total_mape += mape.item() * data.num_graphs

    average_loss = total_loss / len(data_loader.dataset)
    average_node_loss = total_node_loss / len(data_loader.dataset)
    average_reg_loss = total_reg_loss / len(data_loader.dataset)
    average_mape = total_mape / len(data_loader.dataset)  # 平均 MAPE
    
    # 计算相关系数 R
    all_reg_preds_np = np.array(all_reg_preds)
    all_reg_labels_np = np.array(all_reg_labels)
    correlation_matrix = np.corrcoef(all_reg_labels_np.flatten(), all_reg_preds_np.flatten())
    correlation_coefficient = correlation_matrix[0, 1]

    # 计算 RRSE
    rrse = np.sqrt(mean_squared_error(all_reg_labels_np.flatten(), all_reg_preds_np.flatten()) / np.var(all_reg_labels_np)).item()

    return average_loss, average_node_loss, average_reg_loss, average_mape, correlation_coefficient, rrse



def save_checkpoint(epoch, model, optimizer, path):
    torch.save({
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict()
    }, path)
    logging.info(f'Checkpoint saved at {path}')

parser = argparse.ArgumentParser(description="Train a GAT model on a graph dataset.")

parser.add_argument("--lr", type=float, default=0.01, help="Learning rate")
parser.add_argument("--decay", type=float, default=5e-4, help="Weight decay (L2 loss on parameters).")
parser.add_argument("--batch", type=int, default=32, help="Batch size")
parser.add_argument("--neurons", type=int, default=8, help="Number of neurons in the convolution layer.")
parser.add_argument("--num_layers", type=int, default=3, help="Number of graph convolutional layers.")
parser.add_argument("--conv_type", type=str, default="GCN", choices=["GCN", "GAT", "SAGE"], help="Type of graph convolution layer.")
args = parser.parse_args()

learning_rate = args.lr
weight_decay = args.decay
conv_neurons = args.neurons
num_layers = args.num_layers
conv_type = args.conv_type
batch_size = args.batch

log_filename = f"210_{args.lr}_{args.decay}_{args.neurons}_{args.conv_type}_{args.num_layers}_{args.batch}.log"
logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

logging.info(f"Learning rate: {args.lr}")
logging.info(f"Weight decay: {args.decay}")
logging.info(f"Batch size: {args.batch}")
logging.info(f"Number of layers: {args.num_layers}")
logging.info(f"Convolution type: {args.conv_type}")
logging.info(f"Convolution neurons: {args.neurons}")


# Load dataset
dataset = GNNDataset_criticalpath(root='/home/wllpro/llwang/yfdai/HRAE_company/final_dataset')
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Split dataset
train_dataset, test_dataset = train_test_split(dataset, test_size=0.5, random_state=122)
# train_dataset, val_dataset = train_test_split(train_val_dataset, test_size=0.125, random_state=72)
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
# val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=True)

model = SAGE_JK(num_node_features=64, conv_neurons = conv_neurons, num_layers=num_layers, conv_type=conv_type)
model = model.to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=weight_decay)

best_metric = 0.5
best_epoch = 0

for epoch in range(300):
    # 从训练和测试中获取结果，包括相关系数 R 和 RRSE
    train_loss, train_node_loss, train_reg_loss, train_mape, train_r, train_rrse = train(train_loader)
    test_loss, test_node_loss, test_reg_loss, test_mape, test_r, test_rrse = test(test_loader)

    logging.info(f'Epoch {epoch + 1}: Train Loss: {train_loss:.4f}, Train Node Loss: {train_node_loss:.4f}, '
                 f'Train Reg Loss: {train_reg_loss:.4f}, Train MAPE: {train_mape:.4f}, Train R: {train_r:.4f}, '
                 f'Train RRSE: {train_rrse:.4f}, Test Loss: {test_loss:.4f}, Test Node Loss: {test_node_loss:.4f}, '
                 f'Test Reg Loss: {test_reg_loss:.4f}, Test MAPE: {test_mape:.4f}, Test R: {test_r:.4f}, '
                 f'Test RRSE: {test_rrse:.4f}')

    # 如果当前的 MAPE 是最好的，则保存模型检查点
    if test_r > best_metric:
        best_metric = test_r
        best_epoch = epoch + 1
        save_checkpoint(epoch + 1, model, optimizer, f'best_{args.lr}_{args.decay}_{args.neurons}_{args.conv_type}_{args.num_layers}_{args.batch}_{test_r:.4f}_epoch_{epoch + 1}.pth')

# 记录最佳性能的 epoch 和度量值
logging.info(f'Best performance at epoch {best_epoch} with Test MAPE: {best_metric:.4f}')

