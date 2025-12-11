# 파일명: visualize_graph.py (프로젝트 루트에 생성)

import os
import sys
import django

# 1. Django 환경 설정 (models.py 등을 import하기 위해 필수)
# 현재 폴더를 파이썬 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'source.settings')
django.setup()

# 2. 워크플로 가져오기
from corp.agent_workflow import create_agent_workflow

def generate_graph_image():
    print("🎨 Generating workflow graph image...")
    
    try:
        # 워크플로 앱 생성
        app = create_agent_workflow()
        
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