import os
import openai
import base64
import io
from openai import OpenAI
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv("../../../.env")

# OpenAI API setup
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
number_question = os.getenv("NUMBER_QUESTION")


openai.api_key = OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def transcribe_audio(audio_bytes: bytes) -> str:
    """Convert audio bytes to text using OpenAI Whisper."""
    
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "audio.mp3"  # Whisper requires a filename

    transcription = openai.Audio.transcribe(
        model="whisper-1",
        file=audio_file
    )

    return transcription["text"]



def correct_text_or_audio(input_text: str, input_audio: str) -> str:
    """
    Corrects or enhances the input text from a user, handling both text and audio input.
    Uses OpenAI's GPT-4o mini Audio model to process and correct the input.
    
    :param input_text: Optional string input (user-typed text)
    :param input_audio: Optional audio input (bytes format, user-recorded speech)
    :return: Corrected text
    """
    prompt = \
    f"""
    Bạn là một chuyên gia tiếng Việt. Nhiệm vụ của bạn là phát hiện bất thường và chỉnh sửa câu hỏi đầu vào sao cho:
    - Câu sau khi chỉnh sửa đúng ngữ pháp chính tả tiếng việt có dấu
    - Số lượng từ trong câu phải giữ nguyên, không được thêm hoặc bớt.
    - Không thêm bất kỳ từ hay ký tự nào khác ngoài việc chỉnh sửa trong từ.

    Ghi chú: Chỉ trả lời câu hỏi đã chỉnh sửa mà không giải thích gì thêm. Luôn luôn trả lời dưới dạng text
    Ví dụ: 
        Nếu input là "Taij sao càn phải bón phaan howjpj lí cho cây ?", 
        bạn sẽ chỉ output "Tại sao cần phải bón phân cho cây ?"
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
        
        print(messages)
        
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages = messages
        )
        
        corrected_text = completion.choices[0].message
        return corrected_text
    
    except Exception as e:
        print(f"Error: {e}")
        return input_text if input_text else "Lỗi xử lý âm thanh."




# def correct_text_or_audio(input_text: str, input_audio: str) -> str:
#     """
#     Corrects or enhances the input text from a user, handling both text and audio input.
#     Uses OpenAI's GPT-4o mini Audio model to process and correct the input.
    
#     :param input_text: Optional string input (user-typed text)
#     :param input_audio: Optional audio input (bytes format, user-recorded speech)
#     :return: Corrected text
#     """
#     prompt = \
#     f"""
#     Bạn là một chuyên gia tiếng Việt. Nhiệm vụ của bạn là phát hiện bất thường và chỉnh sửa câu hỏi đầu vào sao cho:
#     - Câu sau khi chỉnh sửa đúng ngữ pháp chính tả tiếng việt có dấu
#     - Số lượng từ trong câu phải giữ nguyên, không được thêm hoặc bớt.
#     - Không thêm bất kỳ từ hay ký tự nào khác ngoài việc chỉnh sửa trong từ.

#     Ghi chú: Chỉ trả lời câu hỏi đã chỉnh sửa mà không giải thích gì thêm. Luôn luôn trả lời dưới dạng text
#     Ví dụ: 
#         Nếu input là "Taij sao càn phải bón phaan howjpj lí cho cây ?", 
#         bạn sẽ chỉ output "Tại sao cần phải bón phân cho cây ?"
#     """
    
#     try:
#         messages = [{"role": "system", "content": prompt}]
        
#         if input_text != "":
#             messages.append({"role": "user", "content": [
#                 { 
#                     "type": "text",
#                     "text": input_text

#                 }
#             ]})
#         elif input_audio != "7":
#             messages.append({"role": "user", "content": [
#                 {
#                     "type": "input_audio",
#                     "input_audio": {
#                         "data": input_audio,
#                         "format": "wav"
#                     }
#                 }
#             ]})
#         else:
#             raise ValueError("Either text or audio input must be provided.")
        
#         print(messages)
        
#         completion = client.chat.completions.create(
#             model="gpt-4o-mini-audio-preview-2024-12-17",  # Multi-modal model supporting text and audio
#             modalities=["text", "audio"],
#             audio={"voice": "alloy", "format": "wav"},
#             messages=messages
#         )
        
#         print(completion.choices[0])
#         corrected_text = completion.choices[0].message
#         return corrected_text
    
#     except Exception as e:
#         print(f"Error: {e}")
#         return input_text if input_text else "Lỗi xử lý âm thanh."
    


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
            
        Lưu ý khi generate:
            - Câu hỏi biến thể bắt buộc phải tuyệt đối tương đồng ý nghĩa, cùng cách hỏi, 
            - Trong tất cả câu hỏi biến thể, không có câu nào giống nhau trên 90%, hãy cố gắng để nó đa dạng
        Bạn hãy chỉ output ra đúng 1 python list chứa {number_question} phần tử là các câu hỏi đồng nghĩa.
    """
        
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
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
    

    
def wrong_word_modify(input_text: str):
    
    prompt = \
    f"""
        Bạn là một chuyên gia về việc cố ý viết sai những câu viết đúng. Bạn sẽ nhận đầu vào là 1 python list chứa 5 câu hỏi bằng tiếng Việt
        Tất nhiên cả 5 câu này đều đúng chính tả. Nhiệm vụ của bạn là điều chỉnh cả 5 câu này thành đều sai chính tả với luật sau:
        
        Sai chính tả phải gồm:
            - Sai chính tả  1 số từ tiếng việt, ví dụ người dùng muốn nhập "bón" nhưng vì viết nhanh nên thừa dấu thành "bons" hoặc thiếu dấu "bon".
            - Không có dấu "?"
            - Không có dấu tiếng việt ở một số từ hoặc toàn bộ
            
        Lưu ý khi generate:
            - Bạn chỉ được modify ở scope mỗi từ, không được phép thay đổi cấu trúc câu
            - Mỗi câu sai chính tả đều phải bao gồm cả 3 yếu tố
        Bạn hãy chỉ output ra đúng 1 python list chứa 5 phần tử là các câu hỏi đã được điều chỉnh để sai chính tả.
    """
        
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
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
    
    
    
    
    
    
