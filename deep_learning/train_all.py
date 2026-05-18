import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, models, transforms
import os
import copy
import time
from collections import Counter
from tqdm import tqdm

# ================= 配置区 =================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(CURRENT_DIR, "deep_learning", "final_training_data")
MODEL_SAVE_DIR = os.path.join(CURRENT_DIR, "deep_learning", "models")

NUM_EPOCHS = 50  # 鼻子很难学，多给它几轮
BATCH_SIZE = 16
LEARNING_RATE = 0.001


# =========================================

def print_dataset_stats(dataset, class_names):
    print("-" * 50)
    print(f"📊 数据集体检报告:")
    total_count = len(dataset)
    count_dict = Counter(dataset.targets)
    for idx, count in count_dict.items():
        print(f"   👉 [{class_names[idx]}]: \t{count} 张")
    if total_count == 0: return False
    return True


class LabelSmoothingCrossEntropy(nn.Module):
    def __init__(self, eps=0.1, reduction='mean'):
        super(LabelSmoothingCrossEntropy, self).__init__()
        self.eps = eps
        self.reduction = reduction

    def forward(self, output, target):
        c = output.size()[-1]
        log_preds = torch.nn.functional.log_softmax(output, dim=-1)
        if self.reduction == 'sum':
            loss = -log_preds.sum()
        else:
            loss = -log_preds.sum(dim=-1)
            if self.reduction == 'mean': loss = loss.mean()
        return loss * self.eps / c + (1 - self.eps) * torch.nn.functional.nll_loss(log_preds, target,
                                                                                   reduction=self.reduction)


def get_old_accuracy(model_path):
    if not os.path.exists(model_path): return 0.0
    try:
        checkpoint = torch.load(model_path)
        return checkpoint.get('best_acc', 0.0)
    except:
        return 0.0


def train_model(feature_name):
    print(f"\n\n{'=' * 20}  {feature_name} {'=' * 20}")

    save_path = os.path.join(MODEL_SAVE_DIR, f"{feature_name}.pth")
    old_acc = get_old_accuracy(save_path)
    print(f"🏆 历史最高: {old_acc:.2%}")

    data_dir = os.path.join(DATA_ROOT, feature_name)
    if not os.path.exists(data_dir): return None

    # === 策略核心：针对不同五官定制“眼睛” ===
    if feature_name == "nose_shape":
        print("💡 启用【光影增强模式】(High Contrast + Sharpness)！")
        train_transforms = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.CenterCrop(224),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(10),  # 鼻子不要转太大

            # === 鼻子专用增强 ===
            # 1. 锐化：让模糊的鼻梁变清晰
            transforms.RandomAdjustSharpness(sharpness_factor=2, p=0.5),
            # 2. 高对比度：加深阴影，让立体感更强
            transforms.ColorJitter(brightness=0.1, contrast=0.5, saturation=0.2),

            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        model_arch = "resnet18"  # 回归 ResNet18
        unfreeze_layers = ["layer3", "layer4"]  # 解冻更多层，让它彻底重学鼻子

    elif feature_name == "eyebrow_shape":
        print("💡 启用【几何增强模式】(Affine)！")
        # 眉毛保持 V7 的配置，因为效果很好
        train_transforms = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.CenterCrop(224),
            transforms.RandomHorizontalFlip(),
            transforms.RandomAffine(degrees=15, translate=(0.1, 0.1), scale=(0.9, 1.1), shear=10),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        model_arch = "resnet34"  # 眉毛用 ResNet34
        unfreeze_layers = ["layer4"]

    else:
        # 其他五官 (眼/唇/脸) 保持普通模式
        train_transforms = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.CenterCrop(224),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.1, contrast=0.1),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        model_arch = "resnet18"
        unfreeze_layers = ["layer4"]

    data_transforms = {
        'train': train_transforms,
        'val': transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
    }

    try:
        full_dataset = datasets.ImageFolder(data_dir, data_transforms['train'])
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

    class_names = full_dataset.classes
    if not print_dataset_stats(full_dataset, class_names): return None

    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(full_dataset, [train_size, val_size])

    dataloaders = {
        'train': torch.utils.data.DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0),
        'val': torch.utils.data.DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    }
    dataset_sizes = {'train': len(train_dataset), 'val': len(val_dataset)}
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    # === 模型加载 ===
    if model_arch == "resnet34":
        model = models.resnet34(pretrained=True)
    else:
        model = models.resnet18(pretrained=True)

    # 冻结所有层
    for param in model.parameters():
        param.requires_grad = False

    # 根据策略解冻特定层
    for name, param in model.named_parameters():
        for layer_name in unfreeze_layers:
            if layer_name in name:
                param.requires_grad = True

    model.fc = nn.Sequential(
        nn.Dropout(p=0.5),
        nn.Linear(model.fc.in_features, len(class_names))
    )

    model = model.to(device)
    criterion = LabelSmoothingCrossEntropy(eps=0.1)
    optimizer = optim.SGD(filter(lambda p: p.requires_grad, model.parameters()), lr=LEARNING_RATE, momentum=0.9,
                          weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=NUM_EPOCHS)

    best_model_wts = copy.deepcopy(model.state_dict())
    new_best_acc = 0.0

    print("\n🚀 开始训练...")
    pbar_epoch = tqdm(range(NUM_EPOCHS), desc="Epochs", unit="ep", ncols=100)

    for epoch in pbar_epoch:
        for phase in ['train', 'val']:
            if phase == 'train':
                model.train()
            else:
                model.eval()

            running_corrects = 0

            loader = dataloaders[phase]
            for inputs, labels in loader:
                inputs = inputs.to(device)
                labels = labels.to(device)
                optimizer.zero_grad()
                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)
                    if phase == 'train':
                        loss.backward()
                        optimizer.step()
                running_corrects += torch.sum(preds == labels.data)

            if phase == 'train': scheduler.step()

            epoch_acc = running_corrects.double() / dataset_sizes[phase]

            if phase == 'val':
                if epoch_acc > new_best_acc:
                    new_best_acc = epoch_acc
                    best_model_wts = copy.deepcopy(model.state_dict())
                pbar_epoch.set_postfix({'Val': f'{epoch_acc:.2%}', 'Best': f'{new_best_acc:.2%}'})

    print(f"\n🏁 训练完成: {new_best_acc:.2%}")

    result_info = {'name': feature_name, 'old': old_acc, 'new': new_best_acc, 'action': ''}
    if not os.path.exists(MODEL_SAVE_DIR): os.makedirs(MODEL_SAVE_DIR)

    if new_best_acc >= old_acc:
        torch.save({
            'model_state_dict': best_model_wts,
            'classes': class_names,
            'best_acc': new_best_acc,
            'arch': model_arch
        }, save_path)
        result_info['action'] = '✅ 更新 (Updated)'
    else:
        result_info['action'] = '🛡️ 保留 (Kept Old)'

    return result_info


def run_pipeline():
    if not os.path.exists(DATA_ROOT): return
    features = [f for f in os.listdir(DATA_ROOT) if os.path.isdir(os.path.join(DATA_ROOT, f))]
    results = []
    for feature in features:
        res = train_model(feature)
        if res: results.append(res)

    print("\n\n" + "=" * 70)
    print(f"{'模型名称':<15} | {'旧准确率':<10} | {'新准确率':<10} | {'最终结果'}")
    print("-" * 70)
    for r in results:
        old_s = r['old'].item() if torch.is_tensor(r['old']) else r['old']
        new_s = r['new'].item() if torch.is_tensor(r['new']) else r['new']
        print(f"{r['name']:<15} | {old_s:.2%}     | {new_s:.2%}     | {r['action']}")
    print("=" * 70)


if __name__ == "__main__":
    run_pipeline()