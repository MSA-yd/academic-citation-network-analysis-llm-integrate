"""
测试DashScope API调用
Test DashScope API calls
"""

import os
import sys
import requests
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import Config

def test_dashscope_api():
    """测试DashScope API调用"""
    print("="*60)
    print("DashScope API 测试")
    print("="*60)
    
    # 检查API密钥
    if not Config.DASHSCOPE_API_KEY:
        print("❌ 错误: 未找到DASHSCOPE_API_KEY")
        print("   请确保.env文件中设置了DASHSCOPE_API_KEY")
        return False
    
    api_key = Config.DASHSCOPE_API_KEY
    print(f"✅ API密钥已加载: {api_key[:20]}...{api_key[-10:]}")
    print(f"✅ 模型: {Config.DASHSCOPE_MODEL}")
    print(f"✅ URL: {Config.DASHSCOPE_URL}")
    print()
    
    # 准备请求
    headers = {
        "X-DashScope-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": Config.DASHSCOPE_MODEL,
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": "请用一句话介绍人工智能。"
                }
            ]
        },
        "parameters": {
            "temperature": 0.7,
            "max_tokens": 100
        }
    }
    
    print("📤 发送测试请求...")
    print(f"   模型: {Config.DASHSCOPE_MODEL}")
    print(f"   提示: 请用一句话介绍人工智能。")
    print()
    
    try:
        response = requests.post(
            Config.DASHSCOPE_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )
        
        print(f"📥 响应状态码: {response.status_code}")
        print()
        
        if response.status_code == 200:
            print("✅ API调用成功！")
            print()
            
            # 解析响应
            try:
                result = response.json()
                print("响应结构:")
                print(f"  Keys: {list(result.keys())}")
                print()
                
                # DashScope响应格式
                if "output" in result:
                    output = result["output"]
                    if "choices" in output and len(output["choices"]) > 0:
                        content = output["choices"][0]["message"]["content"]
                        print("生成的回复:")
                        print("-" * 60)
                        print(content)
                        print("-" * 60)
                        return True
                    else:
                        print("⚠️ 响应中没有choices字段")
                        print(f"完整响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
                else:
                    print("⚠️ 响应格式不符合预期")
                    print(f"完整响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析错误: {e}")
                print(f"原始响应: {response.text[:500]}")
                return False
                
        elif response.status_code == 401:
            print("❌ 401 未授权错误")
            print("可能的原因:")
            print("  1. API密钥无效或已过期")
            print("  2. API密钥格式不正确")
            print("  3. API密钥没有访问该模型的权限")
            print()
            print(f"错误详情: {response.text[:500]}")
            return False
            
        elif response.status_code == 400:
            print("❌ 400 请求错误")
            print("可能的原因:")
            print("  1. 请求格式不正确")
            print("  2. 模型名称错误")
            print("  3. 参数格式错误")
            print()
            print(f"错误详情: {response.text[:500]}")
            return False
            
        elif response.status_code == 429:
            print("❌ 429 请求频率限制")
            print("请稍后再试")
            print()
            print(f"错误详情: {response.text[:500]}")
            return False
            
        else:
            print(f"❌ 意外的状态码: {response.status_code}")
            print(f"错误详情: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_dashscope_api()
    print()
    print("="*60)
    if success:
        print("✅ 测试通过！API配置正确。")
    else:
        print("❌ 测试失败！请检查配置。")
    print("="*60)
    sys.exit(0 if success else 1)

