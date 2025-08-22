import sqlite3
import os
from datetime import datetime
import re
from threading import Lock

DB_PATH = 'database.db'
db_lock = Lock()

def init_database():
    """初始化數據庫"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 創建表（如果不存在）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS qa_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            source TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 創建索引以提高查詢性能
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_question ON qa_responses(question)
    ''')
    
    conn.commit()
    conn.close()

def saveresponse(question, answer, source):
    """保存問答對到數據庫"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 檢查是否已存在相同問題
        cursor.execute('SELECT id FROM qa_responses WHERE question = ?', (question,))
        existing = cursor.fetchone()
        
        if existing:
            # 更新現有記錄
            cursor.execute('''
                UPDATE qa_responses 
                SET answer = ?, source = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE question = ?
            ''', (answer, source, question))
            print(f"更新現有記錄: {question}")
        else:
            # 插入新記錄
            cursor.execute('''
                INSERT INTO qa_responses (question, answer, source) 
                VALUES (?, ?, ?)
            ''', (question, answer, source))
            print(f"插入新記錄: {question}")
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"保存到數據庫失敗: {e}")
        return False

def getlocalresponse(question, similarity_threshold=0.6):
    """從數據庫獲取本地回應"""
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 精確匹配
        cursor.execute('SELECT answer, source FROM qa_responses WHERE question = ?', (question,))
        result = cursor.fetchone()
        
        if result:
            conn.close()
            return result[0], result[1]
        
        # 模糊匹配
        cursor.execute('''
            SELECT answer, source FROM qa_responses 
            WHERE question LIKE ? OR ? LIKE question
            ORDER BY created_at DESC LIMIT 1
        ''', (f'%{question}%', f'%{question}%'))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return result[0], result[1]
        
        return None, None

def search_similar_questions(question, limit=5):
    """搜索相似問題"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT question, answer, source FROM qa_responses 
            WHERE question LIKE ? 
            ORDER BY created_at DESC LIMIT ?
        ''', (f'%{question}%', limit))
        
        results = cursor.fetchall()
        conn.close()
        
        return [{"question": r[0], "answer": r[1], "source": r[2]} for r in results]
    except Exception as e:
        print(f"搜索相似問題失敗: {e}")
        return []

def get_all_responses():
    """獲取所有回應（用於調試）"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM qa_responses ORDER BY created_at DESC')
        results = cursor.fetchall()
        conn.close()
        
        return results
    except Exception as e:
        print(f"獲取所有回應失敗: {e}")
        return []

def calculate_similarity(question1, question2):
    """计算两个问题之间的相似度"""
    # 简单的相似度计算方法，可以根据需要改进
    words1 = set(re.findall(r'\w+', question1.lower()))
    words2 = set(re.findall(r'\w+', question2.lower()))
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0

# 初始化數據庫
if __name__ == "__main__":
    init_database()
    print("數據庫初始化完成")

