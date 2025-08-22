#-*- coding:utf-8 -*-
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.serving import WSGIRequestHandler
from flask_cors import CORS
import requests
import time 
from dotenv import load_dotenv
import os
from threading import Lock
from initalDB import saveresponse, getlocalresponse, search_similar_questions #own module
from prompts import prompts # own module
import json
import re

frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
aiinfos_path = os.path.join(frontend_dir, 'aiInfos.json')

with open(aiinfos_path, 'r', encoding='utf-8') as f:
    ai_data = json.load(f)
    aiInfos = ai_data['aiInfos']

load_dotenv()
app = Flask(__name__)
CORS(app)


# API配置
DEEPSEEKV3_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEEPSEEKV3_API_KEY = os.getenv("DEEPSEEKV3_API_KEY")
KIMI_API_URL = "https://openrouter.ai/api/v1/chat/completions"
KIMI_API_KEY = os.getenv("KIMI_API_KEY")
KIMI_API_model = "moonshotai/kimi-k2:free"

def search_local_knowledge(user_message):
    """在本地知識庫中搜索相關資訊"""
    user_message_lower = user_message.lower()
    
    # 首先在數據庫中搜索相似問題
    local_answer, local_source = getlocalresponse(user_message)
    if local_answer:
        return {
            "found": True, #find the source successfully
            "answer": local_answer,
            "source": local_source,
            "type": "database"
        }
    
    # 在aiInfos.json中搜索匹配的AI工具
    matchedTool = []

    for tool in aiInfos:
        tool_name = tool.get('name', '').lower()
        tool_description = tool.get('description', '').lower()
        tool_tags = [tag.lower() for tag in tool.get('tags', [])]
        
        # 檢查是否匹配工具名稱
        if tool_name in user_message_lower or any(tag in user_message_lower for tag in tool_tags):
            matchedTool.append(tool)
    
    if matchedTool:
        return {
            "found": True,
            "matchedTool": matchedTool,
            "type": "json"
        }
    
    return {"found": False}

def generate_response_from_local_tools(user_message, matchedTool):
#     """根據本地匹配的工具生成回應"""
    if not matchedTool:
        return None
    
    # 取前3個最相關的工具
    tools_to_show = matchedTool[:3]
    
    response_parts = []
    for tool in tools_to_show:
        tool_info = f"""名稱：{tool.get('name', '')}
            介紹：{tool.get('description', '')}
            限制：{tool.get('limitations', '')}
            官網超鏈接：{tool.get('website', '')}"""
        response_parts.append(tool_info)
    
    return "\n\n".join(response_parts)


def findmatchedTool(user_message, ai_response):
    """根據用戶消息和AI回應找到匹配的工具"""
    combined_text = (user_message + " " + ai_response).lower()
    print(f"查找匹配工具，合併文本：{combined_text}") #function calling
    print(f"=== 調試信息 ===")
    print(f"user_message: {user_message}")
    print(f"ai_response: {ai_response[:50]}...")
    print(f"aiInfos 數量: {len(aiInfos)}")


    matchedtool = []


    for tool in aiInfos:
        tool_name = tool.get('name', '').lower()
        tool_tags = [tag.lower() for tag in tool.get('tags', [])]

        is_matched = False # Initialize matching flag

        if tool_name and tool_name in combined_text:
            print(f"找到匹配工具：{tool_name}")
            matchedtool.append(matchedAItools(tool))  # add into array
            is_matched = True
            
        
        if not is_matched:
            for tag in tool_tags:
                if tag and tag in combined_text:
                    print(f"找到匹配工具：{tool_name}，標籤：{tag}")
                    matchedtool.append(matchedAItools(tool))
                    is_matched = True
                    break 

    return matchedtool if matchedtool else None

def matchedAItools(tool): #return matched AI tools
    return {
        "name": tool.get('name'),
        "videoUrl": tool.get('videoUrl'),
        "website": tool.get('website'),
        "icon": tool.get('icon'),
        "text": tool.get('text')
    }

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        print(f"用戶消息: {user_message}")
        
        # 步驟1：搜索本地知識庫
        local_result = search_local_knowledge(user_message)
        print(f"本地搜索結果: {local_result}")
        
        if local_result["found"]:
            if local_result["type"] == "database":
                # 直接返回數據庫中的答案
                matchedTool = findmatchedTool(user_message, local_result["answer"])
                print("使用數據庫答案")
                return jsonify({
                    "success": True,
                    "message": local_result["answer"],
                    "source": local_result["source"],
                    "matchedTool": matchedTool
                })
            
            elif local_result["type"] == "json":
                # 使用JSON數據生成答案
                local_answer = generate_response_from_local_tools(user_message, local_result["matchedTool"])
                if local_answer:
                    matchedTool = local_result["matchedTool"][0] if local_result["matchedTool"] else None
                    if matchedTool:
                        matchedTool = {
                            "name": matchedTool.get('name'),
                            "videoUrl": matchedTool.get('videoUrl'),
                            "website": matchedTool.get('website'),
                            "icon": matchedTool.get('icon')
                            
                        }
                    
                    # 保存到數據庫
                    saveresponse(question=user_message, answer=local_answer, source="本地JSON")
                    print("使用JSON數據生成答案")
                    return jsonify({
                        "success": True,
                        "message": local_answer,
                        "source": "本地JSON",
                        "matchedTool": matchedTool
                    })
        
        # 步驟2：本地沒有找到，使用API並增強提示詞
        print("本地未找到，使用API...")
        matchedTool = local_result.get("matchedTool", []) if local_result["found"] else []
       
        
        # 嘗試DeepSeek API
        deepseek_response = call_deepseekv3_api(prompts, user_message)
        if deepseek_response.get('success'):
            return jsonify(deepseek_response)
        
        # 嘗試KIMI API
        kimi_response = call_KIMI_api(prompts, user_message)
        if kimi_response.get('success'):
            return jsonify(kimi_response)
        
        # 所有API都失敗，返回錯誤
        return jsonify({
            "success": False,
            "message": "抱歉，目前無法處理您的請求，請稍後再試。"
        }), 500
        
    except Exception as e:
        print(f"發生錯誤: {e}")
        return jsonify({
            "success": False,
            "message": f"發生錯誤: {str(e)}"
        }), 500

def call_deepseekv3_api(ai_prompt, user_message):   
    try:
        headers = {
            "Authorization": f"Bearer {DEEPSEEKV3_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "deepseek/deepseek-chat-v3-0324:free",
            "messages": [
                {"role": "system", "content": ai_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        response = requests.post(DEEPSEEKV3_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        
        if response.status_code == 200:
            ai_response = response.json()['choices'][0]['message']['content']
           
            # 保存到數據庫
            saveresponse(question=user_message, answer=ai_response, source="DeepSeek V3")
            print("DeepSeek API 成功，已保存到數據庫")
            matchedTool = findmatchedTool(user_message, ai_response)

            return {
                "success": True,
                "message": ai_response,
                "source": "DeepSeek V3",
                "matchedTool": matchedTool
            }
        else:     
           return {"success": False}
    except Exception as e:
        print(f"DeepSeek API 錯誤: {e}")
        return {'success': False}

def call_KIMI_api(ai_prompt, user_message):
    try:
        headers = {
            "Authorization": f"Bearer {KIMI_API_KEY}",    
            "Content-Type": "application/json",
        }

        payload = {
            "model": KIMI_API_model,
            "messages": [
                {"role": "system", "content": ai_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        response = requests.post(KIMI_API_URL, json=payload, headers=headers)    
        response.raise_for_status()

        if response.status_code == 200:
            ai_response = response.json()['choices'][0]['message']['content']
            
            # 保存到數據庫
            saveresponse(question=user_message, answer=ai_response, source="KIMI")
            print("KIMI API 成功，已保存到數據庫")
            matchedTool = findmatchedTool(user_message, ai_response)

            return {
                "success": True,
                "message": ai_response,
                "source": "KIMI",
                "matchedTool": matchedTool
            }
        else:
            return {"success": False}

    except Exception as e:
        print(f"KIMI API 錯誤: {e}")
        return {"success": False}
frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
@app.route('/')
def index():
    return send_from_directory(
        frontend_dir,
        'index_m.html'
    )

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(
        frontend_dir,
        filename
    )

@app.route('/favicon.ico')
def favicon():
    return '', 204  # 返回空響應，狀態碼204

@app.route('/default-icon.png')
def default_icon():
    return '', 204  # 返回空響應，避免404錯誤

@app.route('/admin')
def admin():
    return send_from_directory(
        frontend_dir,  # 改為使用相對路徑變數
        'admin.html'
    )

@app.route('/api/admin/statistics', methods=['GET'])
def get_statistics():
    """獲取統計資訊"""
    try:
        from initalDB import get_statistics
        stats = get_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/records', methods=['GET'])
def get_all_records():
    """獲取所有記錄"""
    try:
        from initalDB import get_all_responses
        records = get_all_responses()
        formatted_records = []
        for record in records:
            formatted_records.append({
                "id": record[0],
                "question": record[1],
                "answer": record[2],
                "source": record[3],
                "created_at": record[4],
                "updated_at": record[5]
            })
        return jsonify({"success": True, "records": formatted_records})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/records', methods=['POST'])
def add_record():
    """新增記錄"""
    try:
        data = request.json
        question = data.get('question')
        answer = data.get('answer')
        source = data.get('source', '手動新增')
        
        if not question or not answer:
            return jsonify({"success": False, "message": "問題和回答不能為空"}), 400
        
        from initalDB import saveresponse
        success = saveresponse(question, answer, source)
        
        if success:
            return jsonify({"success": True, "message": "新增成功"})
        else:
            return jsonify({"success": False, "message": "新增失敗"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/records/<int:record_id>', methods=['PUT'])
def update_record(record_id):
    """更新記錄"""
    try:
        data = request.json
        question = data.get('question')
        answer = data.get('answer')
        source = data.get('source')
        
        from initalDB import update_response
        success = update_response(record_id, question, answer, source)
        
        if success:
            return jsonify({"success": True, "message": "更新成功"})
        else:
            return jsonify({"success": False, "message": "更新失敗"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/records/<int:record_id>', methods=['DELETE'])
def delete_record(record_id):
    """刪除記錄"""
    try:
        from initalDB import delete_response
        success = delete_response(record_id)
        
        if success:
            return jsonify({"success": True, "message": "刪除成功"})
        else:
            return jsonify({"success": False, "message": "刪除失敗"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/search', methods=['GET'])
def search_records():
    """搜尋記錄"""
    try:
        query = request.args.get('query', '')
        source = request.args.get('source', '')
        
        from initalDB import search_records_admin  # 先導入
        results = search_records_admin(query, source)  # 再使用
        
        formatted_results = []
        for record in results:
            formatted_results.append({
                "id": record[0],
                "question": record[1],
                "answer": record[2],
                "source": record[3],
                "created_at": record[4]
            })
        
        return jsonify({"success": True, "results": formatted_results})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    

class CustomRequestHandler(WSGIRequestHandler):
    def log_request(self, code='-', size='-'):
        if self.path in ['/default-icon.png', '/favicon.ico']:
            return  # 不記錄這個請求
        
        super().log_request(code, size)

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5001, debug=False,
#             use_reloader=False, extra_files=['appm.py'], 
#             request_handler=CustomRequestHandler)  # 加入這行

