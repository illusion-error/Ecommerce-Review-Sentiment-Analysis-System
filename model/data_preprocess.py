# model/data_preprocess.py - 超简版
import pandas as pd
import re
import os
from sklearn.model_selection import train_test_split
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_text(text):
    """清洗单个文本"""
    if pd.isna(text):
        return ""
    if not isinstance(text, str):
        text = str(text)
    # 去除URL
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+])+', '', text)
    text = re.sub(r'www\.[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}', '', text)
    # 只保留中文、英文、数字和基本标点
    text = re.sub(r'[^a-zA-Z\u4e00-\u9fa5\d\s\.\?,;:!！？，。、]', ' ', text)
    # 去除多余空格
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def map_star_to_label(star):
    try:
        star = float(star)
        if star <= 2:
            return 0
        elif star >= 4:
            return 1
        else:
            return -1
    except:
        return -1

def process_data():
    """处理数据"""
    input_path = 'data/raw/comments.csv'
    output_dir = 'data/processed'
    os.makedirs(output_dir, exist_ok=True)
    
    # 读取数据
    logger.info("=" * 60)
    logger.info("开始数据预处理")
    logger.info("=" * 60)
    
    # 尝试不同编码
    df = None
    for enc in ['utf-8', 'gbk', 'gb2312', 'gb18030']:
        try:
            df = pd.read_csv(input_path, encoding=enc)
            logger.info(f"成功使用 {enc} 编码读取")
            break
        except:
            continue
    
    if df is None:
        logger.error("无法读取文件")
        return
    
    logger.info(f"原始数据: {len(df)} 条")
    
    # 显示列名
    logger.info(f"列名: {df.columns.tolist()}")
    
    # 查找 content 列
    content_col = None
    star_col = None
    for col in df.columns:
        if 'content' in col.lower() or 'comment' in col.lower():
            content_col = col
        if 'star' in col.lower() or 'score' in col.lower() or 'rating' in col.lower():
            star_col = col
    
    if content_col is None:
        logger.error("找不到评论内容列！")
        logger.info(f"可用列: {df.columns.tolist()}")
        return
    
    if star_col is None:
        logger.error("找不到星级列！")
        logger.info(f"可用列: {df.columns.tolist()}")
        return
    
    logger.info(f"使用内容列: {content_col}")
    logger.info(f"使用星级列: {star_col}")
    
    # 清洗
    logger.info("清洗文本...")
    df['clean_content'] = df[content_col].apply(lambda x: clean_text(x))
    
    # 标签映射
    logger.info("标签映射...")
    df['label'] = df[star_col].apply(lambda x: map_star_to_label(x))
    
    # 过滤
    logger.info("过滤数据...")
    df = df[df['label'] != -1]  # 剔除中性
    df = df[df['clean_content'].str.len() > 1]  # 剔除短文本
    
    # 去重
    before = len(df)
    df = df.drop_duplicates(subset=['clean_content'], keep='first')
    logger.info(f"去重: {before - len(df)} 条")
    
    # 统计
    if len(df) == 0:
        logger.warning("没有数据！")
        return
    
    positive = len(df[df['label'] == 1])
    negative = len(df[df['label'] == 0])
    total = len(df)
    
    logger.info(f"最终数据: {total} 条")
    logger.info(f"  正向: {positive} ({positive/total*100:.1f}%)")
    logger.info(f"  负向: {negative} ({negative/total*100:.1f}%)")
    
    # 保存
    df.to_csv(f'{output_dir}/cleaned_full_data.csv', index=False, encoding='utf-8-sig')
    logger.info("保存 cleaned_full_data.csv")
    
    # 切分
    logger.info("切分数据集...")
    X = df['clean_content']
    y = df['label']
    
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
    )
    
    df.loc[X_train.index].to_csv(f'{output_dir}/train.csv', index=False, encoding='utf-8-sig')
    df.loc[X_val.index].to_csv(f'{output_dir}/val.csv', index=False, encoding='utf-8-sig')
    df.loc[X_test.index].to_csv(f'{output_dir}/test.csv', index=False, encoding='utf-8-sig')
    
    logger.info(f"  训练集: {len(X_train)}")
    logger.info(f"  验证集: {len(X_val)}")
    logger.info(f"  测试集: {len(X_test)}")
    logger.info("=" * 60)
    logger.info("预处理完成！")

if __name__ == "__main__":
    process_data()