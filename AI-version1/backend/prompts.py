import os
import json

def load_ai_infos():
    """載入 aiInfos.json 資料"""
    try:
        # 使用相對路徑找到 aiInfos.json
        current_dir = os.path.dirname(__file__)
        frontend_dir = os.path.join(current_dir, '..', 'frontend')
        aiinfos_path = os.path.join(frontend_dir, 'aiInfos.json')
        
        with open(aiinfos_path, 'r', encoding='utf-8') as f:
            ai_data = json.load(f)
            return ai_data['aiInfos']
    except Exception as e:
        print(f"載入 aiInfos.json 失敗: {e}")
        return []

def generate_ai_tools_context():
    """生成 AI 工具的上下文資訊"""
    ai_infos = load_ai_infos()
    context = "\n\n以下是可用的AI工具資料庫：\n"
    
    for tool in ai_infos:
        context += f"""
工具ID：{tool.get('id', '')}
名稱：{tool.get('name', '')}
介紹：{tool.get('description', '')}
限制：{tool.get('limitations', '')}
官網：{tool.get('website', '')}


---"""
    
    return context

# 基礎 prompt
base_prompts = """你是一個AI助手，專門用於回答有關AI開發和應用的問題。你的目標是提供準確、清晰和有用的答案，幫助用戶解決他們的疑問，回答需满足每个AI工具只保留核心字段，請遵循以下指導原則：
1.回答需簡潔、分行顯示。不使用分隔符和冗余符号，网站不需要重复两次
2.格式爲名稱：AI名稱\n介紹：AI介紹\n優勢：AI優勢\n限制：AI限制\n官网超鏈接：AI官網鏈接
3.只需要介紹3個AI工具，並且每個工具的介紹不超過100字，介紹一個AI工具就換行一次
4.任何與AI無關的東西不在回答範圍之內除了問候語
5.可以使用網絡搜索單，但是提供給你的數據庫中的信息來回答問題
6.不要使用任何的**和--符號
7.網址必須是完整的URL格式，以https://或http://開頭
8.用繁體字回答
9.如果用戶提問的問題是關於AI工具的，請直接回答相關的AI工具信息
10.任何關於自殺，法律，道德和國家安全的問題，統一回復：抱歉，我無法處理你的需求！"""

# 動態生成完整的 prompts
def get_prompts():
    """獲取包含 AI 工具資料的完整 prompt"""
    ai_tools_context = generate_ai_tools_context()
    return base_prompts + ai_tools_context

# 為了向後兼容，保留原有的 prompts 變數
prompts = get_prompts()