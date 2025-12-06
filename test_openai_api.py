"""
测试 OpenAI (ChatAnywhere) API 调用
Test OpenAI API calls with ChatAnywhere
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import Config

try:
    from openai import OpenAI
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    print("❌ 错误: openai 包未安装")
    print("   请运行: pip install openai")
    sys.exit(1)

def test_openai_api():
    """测试 OpenAI API 调用"""
    print("="*60)
    print("OpenAI (ChatAnywhere) API 测试")
    print("="*60)
    print()
    
    # 检查API密钥
    if not Config.OPENAI_API_KEY:
        print("❌ 错误: 未找到 OPENAI_API_KEY")
        print("   请确保 .env 文件中设置了 OPENAI_API_KEY")
        print()
        print("   配置方法:")
        print("   1. 在项目根目录创建 .env 文件")
        print("   2. 添加: OPENAI_API_KEY=your_api_key_here")
        return False
    
    api_key = Config.OPENAI_API_KEY
    print(f"✅ API密钥已加载: {api_key[:20]}...{api_key[-10:]}")
    print(f"✅ 模型: {Config.OPENAI_MODEL}")
    print(f"✅ Base URL: {Config.OPENAI_BASE_URL}")
    print()
    
    # 初始化客户端
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=Config.OPENAI_BASE_URL
        )
        print("✅ OpenAI 客户端初始化成功")
        print()
    except Exception as e:
        print(f"❌ 客户端初始化失败: {e}")
        return False
    
    # 准备测试请求
    test_prompt = "请用一句话介绍人工智能。"
    
    print("📤 发送测试请求...")
    print(f"   模型: {Config.OPENAI_MODEL}")
    print(f"   提示: {test_prompt}")
    print()
    
    try:
        response = client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": test_prompt
                }
            ],
            temperature=0.7,
            max_tokens=100
        )
        
        print("✅ API调用成功！")
        print()
        
        # 解析响应
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            print("生成的回复:")
            print("-" * 60)
            print(content)
            print("-" * 60)
            print()
            
            # 显示响应元数据
            if hasattr(response, 'usage'):
                print("使用统计:")
                if hasattr(response.usage, 'prompt_tokens'):
                    print(f"  提示词 tokens: {response.usage.prompt_tokens}")
                if hasattr(response.usage, 'completion_tokens'):
                    print(f"  完成 tokens: {response.usage.completion_tokens}")
                if hasattr(response.usage, 'total_tokens'):
                    print(f"  总计 tokens: {response.usage.total_tokens}")
                print()
            
            return True
        else:
            print("⚠️ 响应中没有 choices 字段")
            print(f"响应对象: {response}")
            return False
            
    except Exception as e:
        error_type = type(e).__name__
        print(f"❌ API调用失败 ({error_type})")
        print()
        
        # 详细的错误处理
        if "401" in str(e) or "Unauthorized" in str(e):
            print("可能的原因:")
            print("  1. API密钥无效或已过期")
            print("  2. API密钥格式不正确")
            print("  3. API密钥没有访问权限")
        elif "404" in str(e) or "Not Found" in str(e):
            print("可能的原因:")
            print("  1. Base URL 配置错误")
            print("  2. 模型名称不存在")
        elif "429" in str(e) or "rate limit" in str(e).lower():
            print("可能的原因:")
            print("  1. 请求频率过高，触发限流")
            print("  2. 账户余额不足")
        elif "timeout" in str(e).lower():
            print("可能的原因:")
            print("  1. 网络连接问题")
            print("  2. 服务器响应超时")
        else:
            print("未知错误类型")
        
        print()
        print(f"错误详情: {str(e)}")
        print()
        
        # 显示完整错误信息（用于调试）
        import traceback
        print("完整错误堆栈:")
        print("-" * 60)
        traceback.print_exc()
        print("-" * 60)
        
        return False

def test_config_priority():
    """测试 API 优先级配置"""
    print("="*60)
    print("API 优先级配置检查")
    print("="*60)
    print()
    
    has_dashscope = bool(Config.DASHSCOPE_API_KEY and Config.USE_DASHSCOPE)
    has_openai = bool(Config.OPENAI_API_KEY and Config.USE_OPENAI)
    has_openrouter = bool(Config.OPENROUTER_API_KEY)
    
    print("当前配置状态:")
    print(f"  DashScope: {'✅ 已配置' if has_dashscope else '❌ 未配置'}")
    print(f"  OpenAI:    {'✅ 已配置' if has_openai else '❌ 未配置'}")
    print(f"  OpenRouter: {'✅ 已配置' if has_openrouter else '❌ 未配置'}")
    print()
    
    if has_dashscope:
        print("⚠️  注意: DashScope 优先级最高，将优先使用 DashScope")
    elif has_openai:
        print("✅ 将使用 OpenAI (ChatAnywhere) API")
    elif has_openrouter:
        print("⚠️  将使用 OpenRouter API (备选)")
    else:
        print("❌ 没有配置任何 API")
    
    print()

if __name__ == "__main__":
    # 检查配置优先级
    test_config_priority()
    
    # 测试 OpenAI API
    success = test_openai_api()
    
    print()
    print("="*60)
    if success:
        print("✅ 测试通过！OpenAI API 配置正确，可以正常使用。")
    else:
        print("❌ 测试失败！请检查配置和网络连接。")
    print("="*60)
    
    sys.exit(0 if success else 1)

