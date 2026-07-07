# model/train_bert.py - 纯手动训练版（不依赖Trainer）
import torch
from transformers import BertTokenizer, BertForSequenceClassification
from torch.utils.data import DataLoader, Dataset
from torch.optim import AdamW
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import pandas as pd
import numpy as np
import os
import json
import logging
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SentimentDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len=128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = int(self.labels[idx])
        
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_len,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

def train():
    # 创建目录
    os.makedirs('model/weights', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # 加载数据
    train_df = pd.read_csv('data/processed/train.csv')
    val_df = pd.read_csv('data/processed/val.csv')
    test_df = pd.read_csv('data/processed/test.csv')
    
    logger.info(f"训练集: {len(train_df)}, 验证集: {len(val_df)}, 测试集: {len(test_df)}")
    
    if len(train_df) < 2:
        logger.error("训练数据太少！")
        return
    
    # 加载模型
    logger.info("加载BERT模型...")
    tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
    model = BertForSequenceClassification.from_pretrained('bert-base-chinese', num_labels=2)
    
    # 设备
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    logger.info(f"使用设备: {device}")
    
    # 创建数据集
    train_dataset = SentimentDataset(
        train_df['clean_content'].values,
        train_df['label'].values,
        tokenizer
    )
    val_dataset = SentimentDataset(
        val_df['clean_content'].values,
        val_df['label'].values,
        tokenizer
    )
    test_dataset = SentimentDataset(
        test_df['clean_content'].values,
        test_df['label'].values,
        tokenizer
    )
    
    # 数据加载器
    batch_size = min(4, len(train_dataset))
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    # 优化器
    optimizer = AdamW(model.parameters(), lr=2e-5)
    
    # 训练
    epochs = 5
    logger.info(f"开始训练 {epochs} 个epoch...")
    
    best_val_acc = 0
    
    for epoch in range(epochs):
        # 训练
        model.train()
        total_loss = 0
        train_bar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}")
        
        for batch in train_bar:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            
            optimizer.zero_grad()
            outputs = model(input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            train_bar.set_postfix({'loss': f'{loss.item():.4f}'})
        
        avg_loss = total_loss / len(train_loader)
        
        # 验证
        model.eval()
        val_preds = []
        val_labels = []
        
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels = batch['labels'].to(device)
                
                outputs = model(input_ids, attention_mask=attention_mask)
                preds = torch.argmax(outputs.logits, dim=1)
                
                val_preds.extend(preds.cpu().numpy())
                val_labels.extend(labels.cpu().numpy())
        
        val_acc = accuracy_score(val_labels, val_preds)
        
        logger.info(f"Epoch {epoch+1}: Loss={avg_loss:.4f}, Val Acc={val_acc:.4f}")
        
        # 保存最佳模型
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            model.save_pretrained('model/weights/best_model')
            tokenizer.save_pretrained('model/weights/best_model')
            logger.info(f"✓ 保存最佳模型 (Acc: {val_acc:.4f})")
    
    # 加载最佳模型测试
    logger.info("加载最佳模型进行测试...")
    model = BertForSequenceClassification.from_pretrained('model/weights/best_model')
    model.to(device)
    model.eval()
    
    test_preds = []
    test_labels = []
    
    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            
            outputs = model(input_ids, attention_mask=attention_mask)
            preds = torch.argmax(outputs.logits, dim=1)
            
            test_preds.extend(preds.cpu().numpy())
            test_labels.extend(labels.cpu().numpy())
    
    # 计算指标
    if len(test_labels) > 1:
        acc = accuracy_score(test_labels, test_preds)
        precision, recall, f1, _ = precision_recall_fscore_support(
            test_labels, test_preds, average='binary', zero_division=0
        )
        
        logger.info(f"测试结果: Acc={acc:.4f}, Precision={precision:.4f}, Recall={recall:.4f}, F1={f1:.4f}")
        
        results = {'accuracy': acc, 'precision': precision, 'recall': recall, 'f1': f1}
        with open('reports/test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
    else:
        logger.info(f"测试集预测: {test_preds}, 真实: {test_labels}")
    
    logger.info("训练完成！")

if __name__ == "__main__":
    train()