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
            model="gpt-4.1-mini",
            temperature= 0.7,
            input = [ 
                        { "role": "developer", "content": f"""
**Vai trò, nhiệm vụ**:
Bạn là 1 chuyên gia chăm sóc khách hàng làm việc cho Công ty cổ phần Phân Bón Dầu Khí Cà Mau hay Phân Bón Cà Mau, Đạm Cà Mau (PVCFC), 
Nhiệm vụ của bạn là chọn trong bộ câu hỏi dưới dạng Json đã soạn sẵn của công ty về các kiến thức của công ty và phân bón , lấy ra index câu hỏi giống nhất,phù hợp nhất với câu hỏi của người dùng hỏi về các thông tin, sản phẩm, các sự kiện, khuyến mãi của công ty

**Ví dụ**:
Câu hỏi của người dùng: Hướng dẫn cách bón phân NPK Cà Mau 18 8 18 của công ty
Bộ câu hỏi của công ty:
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
}}
]

Thì lúc này bạn sẽ output ra "1", vì document 1 match với câu hỏi gốc về ngữ nghĩa hỏi về cách dùng phân bón 18 8 18, 

**Trường hợp đặc biệt*:
Có một số trường hợp có thể match nhau nhưng không cần giống hoàn toàn như sau thì vẫn cho match vì đây là 1 số trường hợp viết tắt:
- TECH và Tê ECH
- TE và Tê E
- Các nguyên tố hóa học như: S và lưu huỳnh, P và Photpho, Ca và Canxi, K và Kali,...
- AHCM và Anh Hai Cà Mau
- HCM và Hồ Chí Minh
- MVTL và Mùa vàng thắng lớn 
- Urea đồng nghĩa với Urea Bio

**Lưu ý**:
- Nếu như không chọn được câu hỏi nào, hãy output ra -1

**Đây là bộ câu hỏi của công ty :**

{results_docu}

"""},
                        {"role": "user", "content": f"""{question}""" }],
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
    f"""**Nhiệm vụ:**
Bạn là chuyên gia ngôn ngữ của Công ty Phân bón Cà Mau (PVCFC). Bạn cần phát hiện lỗi chính tả, ngữ pháp, và hiệu chỉnh lại câu hỏi đầu vào như sau:

Nếu câu hỏi đã đầy đủ, chỉ sửa lỗi sai chính tả, ngữ pháp.
Nếu câu hỏi quá ngắn, thiếu ý hoặc chưa rõ nghĩa, hãy viết lại cho dài hơn, rõ ràng hơn để có khả năng query ra đáp án chi tiết hơn.
    
**Lưu ý quan trọng:**
- Viết chính xác tiếng Việt, có dấu đúng chuẩn.

Trong câu hỏi đầu vào khả năng cao sẽ là về phân bón, hãy đảm bảo rằng các từ khóa sau viết đúng format (nếu có):
    - Phân bón NPK (Gold) x x x, với x là số, ví dụ: Phân bón NPK 20 10 15, NPK Gold 20 10 10
    - TE
    - K - Kali, P - Photpho, Mg - Magie, B, S - lưu huỳnh, lân, Ca - Canxi
    - N46 Protect / N46 .True / N46 .Golden/ N46 .Plus/ N46 Rich
    - Ure, Urea, Urea Bio ( pay attention, Ure and Urea are different)
    - N.Humate
    - DAP Cà Mau, Kali Cà Mau, Đạm Cà Mau
    - OM CAMAU LIFE / OM CAMAU FARM / OM CAMAU NEED / OM CAMAU HELP / OM CAMAU GREEN / OM CAMAU GOOD / OM CAMAU ECO / OM CAMAU TECH / OM CAMAU RICH / OM CAMAU SUCCESS / OM CAMAU INNOVA / OM CAMAU HAPPY

Các tên này có thể kết hợp với nhau ( có thể viết liền hoặc bởi dấu cộng )
**Một số ví dụ của tên phân bón hay gặp:**:
    - phân bón NPK 15 15 15 + 10S + TE
    - Phân bón N.Humate + TE Cà Mau
    - phân bón NPK 16 16 8 + 13 lưu huỳnh + 1 Magie + 0,1B
    - phân bón OM CAMAU TECH

**Ghi chú**: Chỉ output ra câu hỏi đã chỉnh sửa hoặc câu hỏi gốc nếu không có vấn đề gì mà không giải thích gì thêm, không trả lời cũng như không tư vấn gì
- Nếu có bổ sung thêm ý, bắt buộc vẫn giữ nguyên ý nghĩa câu hỏi, không thêm ý khác vào câu hỏi, dựa vào các ví dụ ở dưới
- Nếu câu hỏi ngắn hơn 6 từ, bắt buộc phải làm dài hơn câu hỏi

Ví dụ: 
    - Nếu input là: "Hứng daanx cho tooii cách bons và lieu luong bón củ phân bon Ca Li Cà Mau ?",
    - bạn sẽ chỉ output: "Hướng dẫn cho tôi cách bón và liều lượng bón của phân bón Kali Cà Mau ?"
    
    - Input: "Địa chỉ"
    - Output: "Địa chỉ công ty Phân Bón Cà Mau ở đâu ?"
    
    - Input: "NPK là gì"
    - Output: "Giới thiệu cho tôi phân bón NPK ?" 
    - Không được ra Output: "Giới thiệu cho tôi phân bón NPK và công dụng của chúng trong nông nghiệp ?" vì thừa ý "công dụng của chúng trong nông nghiệp ", trong câu hỏi gốc k đề cập
    
    - Input: "16 16 8 là gì ?"
    - Output: "Giới thiệu cho tôi phân bón 16 16 8 ?"
    
    - Input: "Công dụng 16 16 8 là gì ?"
    - Output: "Cho tôi biết công dụng của phân bón 16 16 8 như thế nào ?"
    
    - Input: "Xin chào"
    - Output: "Xin chào công ty Phân Bón Cà Mau"
    - Bạn không được output kiểu như "Xin chào, tôi có thể giúp gì cho bạn", bởi vì đây đã là phản hồi, trả lời - điều bạn không được phép
    
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
            model="gpt-4.1",
            temperature= 0.65,
            messages = messages
        )
        
        corrected_text = completion.choices[0].message
        return corrected_text.content
    
    except Exception as e:
        print(f"Error: {e}")
        return input_text if input_text else "Lỗi xử lý âm thanh."


    
    
    
    
    
    
