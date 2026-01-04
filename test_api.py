import requests
import json
import os
import time

# 配置
BASE_URL = "http://localhost:5000/api"
API_KEY = "sk-34tdVDKKpOANgsKWcHYDab7ERtVvEEI8pWv1BAEaIHA6Cxc9"
USER_ID = "test_user_001"
USERNAME = "TestUser"

# 请求头
HEADERS = {
    "X-User-ID": USER_ID,
    "X-Username": USERNAME,
    "X-API-Key": API_KEY
}

def print_result(name, response):
    """打印测试结果"""
    status_icon = "✅" if response.status_code in [200, 201] else "❌"
    print(f"{status_icon} [{name}] Status: {response.status_code}")
    try:
        data = response.json()
        # 截断过长的输出
        print(f"   Response: {str(data)[:200]}...")
        return data
    except:
        print(f"   Response: {response.text[:200]}...")
        return None

def test_status():
    """测试系统状态"""
    print("\n--- Testing System Status ---")
    try:
        response = requests.get(f"{BASE_URL}/status", headers=HEADERS)
        print_result("Status Check", response)
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

def test_upload():
    """测试文件上传"""
    print("\n--- Testing File Upload ---")
    
    # 创建临时CSV文件
    csv_content = "month,revenue,cost\nJan,1000,800\nFeb,1200,850\nMar,1500,900"
    with open("temp_test_data.csv", "w") as f:
        f.write(csv_content)
    
    files = {'file': ('temp_test_data.csv', open('temp_test_data.csv', 'rb'), 'text/csv')}
    
    try:
        # 上传接口也需要鉴权
        # 注意：requests传files时，headers里不能包含Content-Type，它会自动设置
        # 我们把鉴权信息放在 query params 或者 headers (除了Content-Type)
        upload_headers = HEADERS.copy()
        
        response = requests.post(f"{BASE_URL}/upload", headers=upload_headers, files=files)
        print_result("Upload CSV", response)
        
    except Exception as e:
        print(f"❌ Upload Failed: {e}")
    finally:
        # 显式关闭文件句柄
        files['file'][1].close()
        # 清理临时文件
        if os.path.exists("temp_test_data.csv"):
            try:
                os.remove("temp_test_data.csv")
            except Exception as e:
                print(f"Warning: Could not delete temp file: {e}")

def test_template_lifecycle():
    """测试模板全生命周期：生成 -> 列表 -> 详情 -> 删除"""
    print("\n--- Testing Template Lifecycle ---")
    
    # 1. 生成模板
    print("1. Generating Template...")
    html_content = """
    <div class="report-card">
        <h3>Q1 财务摘要</h3>
        <div class="kpi">总收入: ¥1,500,000</div>
        <div class="kpi">净利润: ¥300,000</div>
        <table>
            <tr><th>月份</th><th>收入</th></tr>
            <tr><td>1月</td><td>500,000</td></tr>
            <tr><td>2月</td><td>450,000</td></tr>
        </table>
    </div>
    """
    
    payload = {
        "html_content": html_content,
        "conversation_context": "这是一份季度财务报表，包含收入和利润数据。",
        "conversation_id": "test_conv_123"
    }
    
    response = requests.post(f"{BASE_URL}/templates/generate", headers=HEADERS, json=payload)
    result = print_result("Generate Template", response)
    
    if not result or not result.get("success"):
        print("❌ Template generation failed, skipping remaining tests.")
        return
        
    template_id = result["data"]["template_id"]
    print(f"   Template ID: {template_id}")
    
    # 2. 获取列表
    print("\n2. Listing Templates...")
    response = requests.get(f"{BASE_URL}/templates", headers=HEADERS)
    print_result("List Templates", response)
    
    # 3. 获取详情
    print("\n3. Getting Template Detail...")
    response = requests.get(f"{BASE_URL}/templates/{template_id}", headers=HEADERS)
    detail = print_result("Get Template Detail", response)
    
    if detail and detail.get("success"):
        print("   Vue Template Preview:", detail["data"]["vue_template"][:100])
        print("   Data Schema Keys:", list(detail["data"]["data_schema"].keys()))
        
    # 4. 删除模板
    print("\n4. Deleting Template...")
    response = requests.delete(f"{BASE_URL}/templates/{template_id}", headers=HEADERS)
    print_result("Delete Template", response)
    
    # 5. 再次获取列表验证删除
    print("\n5. Verifying Deletion...")
    response = requests.get(f"{BASE_URL}/templates", headers=HEADERS)
    list_data = response.json()
    found = any(t['id'] == template_id for t in list_data.get('data', []))
    if not found:
        print("✅ Template successfully deleted from list.")
    else:
        print("❌ Template still exists in list.")

if __name__ == "__main__":
    print("🚀 Starting API Tests...")
    print(f"Target: {BASE_URL}")
    print(f"User: {USERNAME} ({USER_ID})")
    
    test_status()
    test_upload()
    test_template_lifecycle()
    
    print("\n🏁 Tests Completed.")
