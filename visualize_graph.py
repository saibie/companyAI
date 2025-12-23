import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'source.settings')
django.setup()

from ai_core.workflow import create_agent_workflow
# [수정 1] 워크플로에 전달할 도구(Tool)들을 임포트합니다.
from ai_core.tools.web_search import search_web
from ai_core.tools.math_tools import calculator_tool

def generate_graph_image():
    print("🎨 Generating workflow graph image...")
    
    try:
        # [수정 2] 함수가 요구하는 tools 리스트를 정의합니다.
        # 시각화가 목적이므로 대표적인 도구 몇 개만 리스트로 만들어 전달하면 됩니다.
        tools = [search_web, calculator_tool]
        
        # [수정 3] create_agent_workflow 함수에 tools 인자를 전달합니다.
        app = create_agent_workflow(tools)
        
        # Mermaid PNG 데이터 생성
        # (주의: 인터넷 연결이 필요할 수 있습니다. LangGraph가 mermaid.ink API를 사용할 수 있음)
        png_data = app.get_graph().draw_mermaid_png()
        
        output_filename = "agent_workflow_diagram.png"
        with open(output_filename, "wb") as f:
            f.write(png_data)
            
        print(f"✅ Success! Graph saved to: ./{output_filename}")
        
    except Exception as e:
        print(f"❌ Error generating graph: {e}")
        print("Tip: 'pip install grandalf' might help if using draw_ascii, but for PNG ensure internet access.")

if __name__ == "__main__":
    generate_graph_image()