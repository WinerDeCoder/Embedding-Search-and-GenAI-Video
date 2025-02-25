import os
import openai
from openai import OpenAI
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv("../../.env")

# OpenAI API setup
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
number_question = os.getenv("NUMBER_QUESTION")


openai.api_key = OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

# Function to correct or enhance the input text using GPT
def correct_text_with_gpt(input_text: str) -> str:
    prompt = \
    f"""
    Bạn là một chuyên gia tiếng Việt. Nhiệm vụ của bạn là phát hiện bất thường và chỉnh sửa câu hỏi đầu vào sao cho:
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
            model="gpt-4o-mini",
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



# Define structured output
class Question_List(BaseModel):
    quest_list: list[str]

def generate_variant_question(input_text: str):
    
    prompt = \
    f"""
            Tôi đang thiết kế một hệ thống hỏi đáp, về cơ bản, nó sẽ nhận input từ user là 1 câu hỏi, sau đó dùng vector search để tìm câu hỏi có sẵn giống nhất trong database,
        từ đó sẽ đối chiếu để lấy ra câu trả lời cho câu hỏi có sẵn đó. Chính vì vậy, tôi cần test bằng cách generate ra những câu hỏi biến thế từ câu hỏi gôc mà user có thể sẽ đặt.
        
        Bạn là một chuyên gia ngữ pháp tiếng việt, nhiệm vụ của bạn là viết ra {number_question} câu hỏi biến thể đồng nghĩa với câu hỏi gốc mà user cung cấp:
            - Bạn có thể đổi cách hỏi
            - Bạn có thể dùng những từ đồng nghĩa
            - Bạn có thể dùng thêm những từ địa phương ở Việt Nam
            - Bạn có thể thêm bớt 1 số từ trong câu hỏi gốc mà không làm thay đổi ý nghĩa câu
        ***Đặc biệt, câu hỏi biến thể có thể***:
            - Sai chính tả  1 số từ tiếng việt, ví dụ người dùng muốn nhập "bón" nhưng vì viết nhanh nên thừa dấu thành "bons" hoặc thiếu dấu "bon".
            - Không có dấu "?"
            - Không có dấu tiếng việt ở một số từ hoặc toàn bộ
            
        Lưu ý khi generate:
            - Câu hỏi biến thể bắt buộc phải tuyệt đối tương đồng ý nghĩa, cùng cách hỏi, 
            - ***Đặc biệt phải có***: 
                + Với những trường hợp đặc biệt cho câu hỏi biến thể như trên ( sai chính tả, không dấu,....), hãy cho phép 50% trên tổng số câu vào trường hợp này, còn 50% sẽ luôn đúng toàn bộ ngữ pháp
                + ***Ở các câu đặc biệt, bắt buộc phải có ít nhất 1 từ sai chính tả như đã define***
                + Để cố ý viết sai chính tả, hay random một số từ để viết dấu tiếng việt cần unikey nhưng cố ý không set. Ví dụ "bón" thành "bon".
            - Assume sao cho nếu dùng phương pháp embedding vector và so sánh cosine thì vector câu hỏi biến thể và câu hỏi gốc phải đạt ít nhất 0.7 ( cosine range từ -1 tới 1)
            - Trong tất cả câu hỏi biến thể, không có câu nào giống nhau trên 90%
        Bạn hãy chỉ output ra đúng 1 python list chứa {number_question} phần tử là các câu hỏi đồng nghĩa.
    """
        
    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "developer", "content": f"{prompt}"},
            {
                "role": "user",
                "content": f"{input_text}"
            }
        ],
        response_format = Question_List
    )
    
    output_list = completion.choices[0].message
    
    if (output_list.refusal):
        return ["-1"]
    else:
        return output_list.parsed
    
    
    
    
    
    
