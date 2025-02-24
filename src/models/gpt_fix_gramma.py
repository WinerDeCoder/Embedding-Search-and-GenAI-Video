import os
import openai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv("../../.env")

# OpenAI API setup
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


# Function to correct or enhance the input text using GPT
def correct_text_with_gpt(input_text: str) -> str:
    prompt = f"""Bạn là một chuyên gia tiếng Việt. Nhiệm vụ của bạn là phát hiện bất thường và chỉnh sửa câu hỏi đầu vào sao cho:
    - Câu sau khi chỉnh sửa đúng ngữ pháp chính tả tiếng việt có dấu
    - Số lượng từ trong câu phải giữ nguyên, không được thêm hoặc bớt.
    - Không thêm bất kỳ từ hay ký tự nào khác ngoài việc chỉnh sửa trong từ.

    Ghi chú: Chỉ trả lời câu hỏi đã chỉnh sửa mà không giải thích gì thêm.
    Ví dụ: 
        Nếu input là "Taij sao càn phải bón phaan howjpj lí cho cây ?", 
        bạn sẽ chỉ output "Tại sao cần phải bón phân cho cây ?"
    """
    
    try:
        
        completion = client.chat.completions.create(
            model="gpt-4-mini",
            messages=[
                {"role": "developer", "content": f"{prompt}"},
                {
                    "role": "user",
                    "content": f"{input_text}"
                }
            ]
        )
        
        corrected_text = completion.choices[0].message
        return corrected_text
    except Exception as e:
        # Fallback to the original text
        return input_text  
