import os
import openai
import base64
import io
from openai import OpenAI
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv("../.env")

# OpenAI API setup
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
number_question = os.getenv("NUMBER_QUESTION")


openai.api_key = OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def transcribe_audio(audio_bytes: bytes) -> str:
    """Convert audio bytes to text using OpenAI Whisper."""
    
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "audio.mp3"  # Whisper requires a filename

    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        prompt="Tiếng Việt, P V C F C, phân bón NPK, Ure, Kali, Canxi, Photpho, Plus, N.Humate, NPK Cà Mau, Gold, T E.\
                OM-CAMAU-ECO, N46. Protect, OM CAMAU RICH, INNOVA, GOOD, DAP, Magie, N46, cộng B, Lưu Huỳnh, +, AHCM, HCM "
    )

    return transcription.text


class Most_Similar(BaseModel):
    index: int 

def the_most_similar_doc(question, results):
    
    results_docu = []
    for index, docu in enumerate(results["documents"][0]):
        results_docu.append({
            "index": index,
            "document": docu
        })
    
    
    completion = client.responses.parse(
            model="gpt-4o-mini",
            temperature= 0.7,
            input = [ 
                        { "role": "developer", "content": f"""
**Vai trò, nhiệm vụ**:
Bạn là 1 chuyên gia làm việc cho Công ty cổ phần Phân Bón Dầu Khí Cà Mau hay Phân Bón Cà Mau (PVCFC), nhiệm vụ của bạn là xác định matching câu hỏi gốc - câu hỏi biến thể dựa trên meaning và các từ, số giống nhau

Người dùng sẽ gửi cho bạn 1 câu hỏi gốc, và 1 json object - mỗi phần tử chứa 1 câu hỏi và index tương ứng. Nhiệm vụ của bạn là so sánh câu hỏi gốc và các câu hỏi trong json. Sau đó trả ra index của câu hỏi giống câu hỏi gốc nhất , nếu không có sẽ trả về -1

**Ví dụ**:
Câu hỏi gốc: Hướng dẫn cách bón phân NPK Cà Mau 18 8 18

Các câu hỏi trong json object:
[{{
    "index": 0,
    "document": "Hướng dãn cho tôi cách bón phân NPK Cà Mau 18 18 8"  
}},
{{
    "index": 1,
    "document": "Hướng dãn cho tôi cách bón phân cho phân bón NPK Cà Mau 18 8 18"  
}},
{{
    "index": 2,
    "document": "Phân bón NPK Cà Mau 18 8 18 có những thành phần gì"  
}},
{{
    "index": 3,
    "document": "Phân bón NPK Cà Mau 18 8 18 + 10S + TE có những thành phần gì"  
}}
]

Thì lúc này bạn sẽ output ra "1", vì document 1 match với câu hỏi gốc về ngữ nghĩa hỏi về cách dùng phân bón 18 8 18, 
còn index 0 dù đúng ngữ nghĩa nhưng bị sai tên thành 18 18 8 nên không match
Còn index 2 tuy match sản phẩm 18 8 18 nhưng ngữ nghĩa câu hỏi không giống nhau
Còn index 3 tuy match sản phẩm 18 8 18 nhưng có thêm + 10S + TE, suy ra khác loại nên không match

**Trường hợp đặc biệt*:
Có một số trường hợp có thể match nhau nhưng không cần giống hoàn toàn như sau thì vẫn cho match vì đây là 1 số trường hợp viết tắt:
- TECH và Tê ECH
- TE và Tê E
- Các nguyên tố hóa học như: S và lưu huỳnh, P và Photpho, Ca và Canxi, K và Kali,...
- AHCM và Anh Hai Cà Mau
- HCM và Hồ Chí Minh
- MVTL và Mùa vàng thắng lớn 

**Lưu ý**:
- Các câu hỏi sẽ đa số về phân bón với các kí hiệu phân bón
- So sánh ở mức độ giống nhau về cả ngữ nghĩa và các chữ trùng
- Bắt buộc phải trả về index trong tập json hoặc -1, không được trả về index nào khác
"""},
                        {"role": "user", "content": f"""Đây là câu hỏi gốc: {question}
Đây là list các json object chứa câu hỏi và index tương ứng: {results_docu}""" }],
            text_format=Most_Similar,
        )
            
    return completion.output_parsed.index

def correct_text_or_audio(input_text: str, input_audio: str) -> str:
    """
    Corrects or enhances the input text from a user, handling both text and audio input.
    Uses OpenAI's GPT-4o mini Audio model to process and correct the input.
    
    :param input_text: Optional string input (user-typed text)
    :param input_audio: Optional audio input (bytes format, user-recorded speech)
    :return: Corrected text
    """
    prompt = \
    f"""**Nhiệm vụ**: Bạn là một chuyên gia tiếng Việt làm việc cho Công ty cổ phần Phân Bón Dầu Khí Cà Mau hay Phân Bón Cà Mau (PVCFC). Nhiệm vụ của bạn là phát hiện bất thường và chỉnh sửa câu hỏi đầu vào sao cho:
    - Câu sau khi chỉnh sửa đúng ngữ pháp chính tả tiếng việt có dấu, trừ những từ chuyên ngành về phân bón, nông nghiệp.
    - Số lượng từ trong câu phải giữ nguyên, không được thêm hoặc bớt.
    
**Lưu ý quan trọng:**
Trong câu hỏi đầu vào khả năng cao sẽ là về phân bón, hãy đảm bảo rằng các từ khóa sau viết đúng format (nếu có):
    - Phân bón NPK (Gold) x x x, với x là số, ví dụ: Phân bón NPK 20 10 15, NPK Gold 20 10 10
    - TE
    - K - Kali, P - Photpho, Mg - Magie, B, S - lưu huỳnh, lân, Ca - Canxi
    - N46 Protect / N46 .True / N46 .Golden/ N46 .Plus/ N46 Rich
    - Urea Bio
    - N.Humate
    - DAP Cà Mau, Kali Cà Mau, Đạm Cà Mau
    - OM CAMAU LIFE / OM CAMAU FARM / OM CAMAU NEED / OM CAMAU HELP / OM CAMAU GREEN / OM CAMAU GOOD / OM CAMAU ECO / OM CAMAU TECH / OM CAMAU RICH / OM CAMAU SUCCESS / OM CAMAU INNOVA / OM CAMAU HAPPY

Các tên này có thể kết hợp với nhau ( có thể viết liền hoặc bởi dấu cộng )
**Một số ví dụ của tên phân bón hay gặp:**:
- phân bón NPK 15 15 15 + 10S  + TE
- Phân bón N.Humate + TE Cà Mau
- phân bón NPK 20 15 7 + 1 Magie + TE
- phân bón NPK Gold 20 20 15 + TE
- phân bón NPK 16 16 8 + 13 lưu huỳnh + 1 Magie + 0,1B
- phân bón OM CAMAU TECH

**Ghi chú**: Chỉ trả lời câu hỏi đã chỉnh sửa mà không giải thích gì thêm. Luôn luôn trả lời dưới dạng text
Ví dụ: 
    - Nếu input là: "Hứng daanx cho tooii cách bons và lieu luong bón củ phân bon Ca Li Cà Mau ?",
    - bạn sẽ chỉ output: "Hướng dẫn cho tôi cách bón và liều lượng bón của phân bón Kali Cà Mau ?"
    """
    
    try:
        messages = [{"role": "system", "content": prompt}]
        
        # Case audio
        if input_text == "":
            
            # Decode base64 string to bytes
            audio_bytes = base64.b64decode(input_audio)
            
            transcription_text = transcribe_audio(audio_bytes)
            
            messages.append({
                    "role": "user",
                    "content": transcription_text
                })
            
        else:
            
            messages.append({
                    "role": "user",
                    "content": input_text
                })
            
            #raise ValueError("Either text or audio input must be provided.")
        
        #print(messages)
        
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature= 0.7,
            messages = messages
        )
        
        corrected_text = completion.choices[0].message
        return corrected_text.content
    
    except Exception as e:
        print(f"Error: {e}")
        return input_text if input_text else "Lỗi xử lý âm thanh."


    
    
    
    
    
    
