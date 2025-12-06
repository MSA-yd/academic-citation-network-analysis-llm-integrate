"""
使用DashScope官方SDK测试API调用
Test DashScope API using official SDK
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import Config

try:
    from dashscope import Generation
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    print("⚠️ DashScope SDK未安装，将使用REST API方式测试")

def test_with_sdk():
    """使用官方SDK测试"""
    print("="*60)
    print("使用DashScope SDK测试")
    print("="*60)
    
    if not Config.DASHSCOPE_API_KEY:
        print("❌ 错误: 未找到DASHSCOPE_API_KEY")
        return False
    
    api_key = Config.DASHSCOPE_API_KEY
    print(f"✅ API密钥: {api_key[:20]}...{api_key[-10:]}")
    print(f"✅ 模型: {Config.DASHSCOPE_MODEL}")
    print()
    
    try:
        messages = [
            {"role": "user", "content": "请用一句话介绍人工智能。"}
        ]
        
        print("📤 发送请求...")
        response = Generation.call(
            model=Config.DASHSCOPE_MODEL,
            messages=messages,
            api_key=api_key
        )
        
        print(f"📥 状态码: {response.status_code}")
        print()
        
        if response.status_code == 200:
            print("✅ API调用成功！")
            print()
            print("生成的回复:")
            print("-" * 60)
            print(response.output.choices[0].message.content)
            print("-" * 60)
            return True
        else:
            print(f"❌ API调用失败")
            print(f"错误信息: {response.message}")
            if hasattr(response, 'request_id'):
                print(f"Request ID: {response.request_id}")
            return False
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if SDK_AVAILABLE:
        success = test_with_sdk()
    else:
        print("请先安装DashScope SDK: pip install dashscope")
        success = False
    
    print()
    print("="*60)
    if success:
        print("✅ 测试通过！")
    else:
        print("❌ 测试失败！")
    print("="*60)
    sys.exit(0 if success else 1)

